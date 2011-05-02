#include "flog.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <unistd.h>
#include <netdb.h>
#include <stdbool.h>
#include <sys/time.h>

typedef enum { Flog_TStream, Flog_TServer } Flog_TargetType;

typedef struct Flog_STarget
{
	Flog_TargetType type; 
	uint8_t filter; 
	void (*log_callback)(struct Flog_STarget* target, const char* file, 
		uint32_t lineNumber, Flog_Severity severity, const char* message);
	
	int sockfd; /* for servers */
	FILE* stream; /* for streams */
} Flog_Target;

#define FLOG_MAX_TARGETS 0xff

typedef struct {
	char* applicationName;
	Flog_Target targets[FLOG_MAX_TARGETS];
	int numTargets;
} Flog_Internal;

static Flog_Internal internal;

const char* Flog_SeverityToString(Flog_Severity severity)
{
	static char *severityString[] = { "D1", "D2", "D3", "VV", "II", "WW", "EE", "FF", "??" };
	for(int i = 0; i < 8; i++){
		if(((int)severity >> i) & 1){
			return severityString[i];
		}
	}

	return severityString[8];
}

// Write exactly 'numbytes' bytes to the stream
bool Flog_WriteExactly(int sockfd, const char* msg, int numbytes)
{
	int left = numbytes;
	while(left > 0){
		int wrote = write(sockfd, msg, left);

		if(wrote <= 0){
			return false;
		}

		left -= wrote;
	}

	return false;
}

bool Flog_WriteUint32(int sockfd, uint32_t num)
{
	num = htonl(num);
	return Flog_WriteExactly(sockfd, (char*)&num, 4);
}

// 64 bit integer to network byte order
uint64_t Flog_Htonll(uint64_t in) {
	int test = 1;
	if(((char*)&test)[0]){
		// little endian, reverse
		uint64_t ret = 0;
		for(int i = 0; i < 8; i++){
			((char*)&ret)[7 - i] = ((char*)&in)[i];
		}
		return ret;
	}

	// already big endian (ie. network byte order)
	return in;
}

uint64_t Flog_GetTimeStamp()
{
	struct timeval val;
	gettimeofday(&val, NULL);
	return (uint64_t)val.tv_sec * 1000LL + (uint64_t)val.tv_usec;
}

bool Flog_WriteUint64(int sockfd, uint64_t num)
{
	num = Flog_Htonll(num);
	return Flog_WriteExactly(sockfd, (char*)&num, 8);
}

void Flog_WriteString(int sockfd, const char* str)
{
	int len = strlen(str);
	Flog_WriteUint32(sockfd, len);
	Flog_WriteExactly(sockfd, str, len);
}

void Flog_LogToServer(Flog_Target* target, const char* file, 
	uint32_t lineNumber, Flog_Severity severity, const char* message)
{
	uint8_t s = (uint8_t)severity;

	Flog_WriteString(target->sockfd, internal.applicationName);
	Flog_WriteUint64(target->sockfd, Flog_GetTimeStamp());
	Flog_WriteString(target->sockfd, file);
	Flog_WriteUint32(target->sockfd, lineNumber);
	write(target->sockfd, &s, 1);
	Flog_WriteString(target->sockfd, message);
}

void Flog_LogToStream(Flog_Target* target, const char* file, 
	uint32_t lineNumber, Flog_Severity severity, const char* message)
{
	fprintf(target->stream, "[%s] %s %d: %s\n", Flog_SeverityToString(severity), file, lineNumber, message);
}

void Flog_CopyString(const char* source, char** target)
{
	if(*target){
		free(*target);
	}

	int size = strlen(source) + 1;
	*target = malloc(size);
	memcpy(*target, source, size);
	(*target)[size - 1] = '\0';
}

void Flog_Init(const char* applicationName)
{
	Flog_CopyString(applicationName, &internal.applicationName);
}

int Flog_AddTargetServer(const char* address, uint16_t port, uint8_t filter)
{
	Flog_Target* target = &internal.targets[internal.numTargets];
	
	target->type = Flog_TServer;
	target->filter = filter;
	target->log_callback = Flog_LogToServer;

	target->sockfd = socket(AF_INET, SOCK_STREAM, 0);

	if (!target->sockfd < 0){
		goto error;
	}

	struct hostent* server = gethostbyname(address);
	if (server == NULL) {
		goto error;
	}

	struct sockaddr_in serv_addr;
	memset(&serv_addr, 0, sizeof(serv_addr));

	serv_addr.sin_family = AF_INET;

	memcpy((char *)server->h_addr_list[0], (char *)&serv_addr.sin_addr.s_addr, server->h_length);

	serv_addr.sin_port = htons(port);

	if (connect(target->sockfd, (struct sockaddr *) &serv_addr, sizeof(serv_addr)) < 0) {
		goto error;
	}
	
	internal.numTargets++;

	return 1;

	error:
	memset(target, 0, sizeof(Flog_Target));
	return 0;
}

void Flog_AddTargetStream(FILE* stream, uint8_t filter)
{
	Flog_Target* target = &internal.targets[internal.numTargets];
	
	target->type = Flog_TStream;
	target->filter = filter;
	target->log_callback = Flog_LogToStream;
	target->stream = stream;

	internal.numTargets++;
}

int Flog_AddTargetFile(const char* filename, uint8_t filter)
{
	FILE* f = fopen(filename, "w+");
	if(!f){
		return 0;
	}

	Flog_AddTargetStream(f, filter);
	return 1;
}


void Flog_Log(const char* file, uint32_t lineNumber, Flog_Severity severity, const char* format, ...)
{
	va_list fmtargs;
	char buffer[4096];

	buffer[sizeof(buffer) - 1] = '\0';

	va_start(fmtargs, format);
	vsnprintf(buffer, sizeof(buffer) - 1, format, fmtargs);
	va_end(fmtargs);
	
	for(int i = 0; i < internal.numTargets; i++){
		if((uint8_t)severity & internal.targets[i].filter){
			internal.targets[i].log_callback(&internal.targets[i], file, lineNumber, severity, buffer);
		}
	}
}
