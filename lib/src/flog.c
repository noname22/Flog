// FIXME check number of targets
// FIXME handle shutdown

#define ABlack "0"
#define ARed "1"
#define AGreen "2"
#define AYellow "3"
#define ABlue "4"
#define AMagenta "5"
#define ACyan "6"
#define AWhite "7"

#define AnsiColorIn(__color) "\033[9" __color "m"
#define AnsiColorOut "\033[39m"
#define AnsiColorBGIn(__color) "\033[4" __color "m"
#define AnsiColorBGOut "\033[49m"

#define AnsiBoldIn "\033[1m"
#define AnsiBoldOut "\033[22m"
#define AnsiUnderlineIn "\033[4m" 
#define AnsiUnderlineOut "\033[24m"
#define AnsiInvertIn "\033[7m" 
#define AnsiInvertOut "\033[27m"

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
#include <time.h>

typedef enum { Flog_TStream, Flog_TServer } Flog_TargetType;

typedef struct Flog_STarget
{
	Flog_TargetType type; 
	uint8_t filter; 
	void (*log_callback)(struct Flog_STarget* target, const char* file, 
		uint32_t lineNumber, Flog_Severity severity, const char* message);
	
	int sockfd; /* for servers */
	FILE* stream; /* for streams */
	bool useAnsiColors;
} Flog_Target;

#define FLOG_MAX_TARGETS 0xff

typedef struct {
	char* applicationName;
	Flog_Target targets[FLOG_MAX_TARGETS];
	int numTargets;
} Flog_Internal;

static Flog_Internal internal;

int Flog_SeverityToIndex(Flog_Severity severity)
{
	for(int i = 0; i < 8; i++){
		if(((int)severity >> i) & 1){
			return i;
		}
	}

	return 8;
}

const char* Flog_SeverityToString(Flog_Severity severity)
{
	static char *severityString[] = { "D1", "D2", "D3", "VV", "II", "WW", "EE", "FF", "??" };
	return severityString[Flog_SeverityToIndex(severity)];
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

bool Flog_ReadExactly(int sockfd, char* buffer, int numbytes)
{
	int left = numbytes;
	while(left > 0){
		int r = read(sockfd, buffer, left);

		if(r <= 0){
			return false;
		}

		left -= r;
		buffer += r;
	}
	
	return true;
}

bool Flog_WriteUint32(int sockfd, uint32_t num)
{
	num = htonl(num);
	return Flog_WriteExactly(sockfd, (char*)&num, 4);
}

bool Flog_ReadUint32(int sockfd, uint32_t* out)
{
	if(!Flog_ReadExactly(sockfd, (char*)out, 4)){
		return false;
	}
	*out = ntohl(*out);
	return true;
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
	return (uint64_t)val.tv_sec * 1000LL + (uint64_t)val.tv_usec / 1000LL;
}

bool Flog_WriteUint64(int sockfd, uint64_t num)
{
	num = Flog_Htonll(num);
	return Flog_WriteExactly(sockfd, (char*)&num, 8);
}

bool Flog_ReadString(int sockfd, char* buffer, int max)
{
	// FIXME care about max :x
	uint32_t len;
	Flog_ReadUint32(sockfd, &len);
	Flog_ReadExactly(sockfd, buffer, len);
	buffer[len] = '\0';
	return true;
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
	static char *colorString[] = { AnsiColorIn(ACyan), AnsiColorIn(ACyan), AnsiColorIn(ACyan), AnsiColorIn(AMagenta), 
		AnsiColorIn(AGreen), AnsiColorIn(AYellow), AnsiColorIn(ARed), AnsiColorIn(ARed), "" };
	static char ansiColorOut[] = AnsiColorOut;
	char* colorIn = colorString[8], *colorOut = colorString[8], *fileIn = colorString[8], *fileOut = colorString[8];

	if(target->useAnsiColors){
		colorOut = ansiColorOut;
		colorIn = colorString[Flog_SeverityToIndex(severity)];
		fileIn = AnsiBoldIn;
		fileOut = AnsiBoldOut;
	}

	struct timeval tv;
	gettimeofday(&tv, NULL);
	struct tm* t = localtime(&tv.tv_sec);

	int headerLen = fprintf(target->stream, "%02d:%02d:%02d [%s%s%s] %s%s%s:%d ", 
		t->tm_hour, t->tm_min, t->tm_sec,
		colorIn, Flog_SeverityToString(severity), colorOut, 
		fileIn, file, fileOut, lineNumber);

	for(int i = 0; i < 52 - headerLen; i++){
		putc(' ', target->stream);
	}

	fprintf(target->stream, "%s\n", message);
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
	
	struct timeval tv = {10, 0};
	setsockopt(target->sockfd, SOL_SOCKET, SO_RCVTIMEO, (char*)&tv, sizeof(struct timeval));

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
	
	// Handshake

	Flog_WriteString(target->sockfd, "flog");
	Flog_WriteString(target->sockfd, "logger");
	Flog_WriteUint32(target->sockfd, 1);

	char buffer[1024];

	Flog_ReadString(target->sockfd, buffer, sizeof(buffer));
	if(strcmp(buffer, "ok")){
		goto error;
	}

	internal.numTargets++;

	return 1;

	error:
	memset(target, 0, sizeof(Flog_Target));
	return 0;
}

void Flog_AddTargetStream(FILE* stream, uint8_t filter, int useAnsiColors)
{
	Flog_Target* target = &internal.targets[internal.numTargets];
	
	target->type = Flog_TStream;
	target->filter = filter;
	target->log_callback = Flog_LogToStream;
	target->stream = stream;
	target->useAnsiColors = useAnsiColors;

	internal.numTargets++;
}

int Flog_AddTargetFile(const char* filename, uint8_t filter)
{
	FILE* f = fopen(filename, "w+");
	if(!f){
		return 0;
	}

	Flog_AddTargetStream(f, filter, false);
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
