#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netdb.h>
#include <stdint.h>

#include <flog.h>

void error(const char *msg)
{
    perror(msg);
    exit(0);
}

int main()
{
	Flog_Init("Testapp");

	Flog_AddTargetStream(stdout, Flog_SDebug1 |Flog_SDebug2 | Flog_SDebug3 | Flog_SVerbose | Flog_SInfo | Flog_SWarning, 1);
	Flog_AddTargetStream(stderr, Flog_SError | Flog_SFatal, 1);
	
	if( !Flog_AddTargetServer("localhost", Flog_DefaultPort, Flog_SAll) ){
		printf("couldn't connect to server\n");
		return 1;
	}

	FlogD1("debug level 1");
	FlogD2("debug level 2");
	FlogD3("debug level 3");
	FlogD("debug default level");
	FlogV("verbose");
	FlogI("info");
	FlogW("warning");
	FlogE("error");
	FlogF("fatal error");

	return 0;
}

#if 0
int main(int argc, char** argv)
{
	int sockfd, portno, n;
	struct sockaddr_in serv_addr;
	struct hostent *server;
	uint32_t len;
	int i;

	char buffer[256];

	if (argc < 3) {
		fprintf(stderr,"usage %s hostname port\n", argv[0]);
		return 1;
	}

	portno = atoi(argv[2]);
	sockfd = socket(AF_INET, SOCK_STREAM, 0);

	if (sockfd < 0){
		error("ERROR opening socket");
	}

	server = gethostbyname(argv[1]);

	if (server == NULL) {
		fprintf(stderr,"ERROR, no such host\n");
		exit(0);
	}

	bzero((char *) &serv_addr, sizeof(serv_addr));

	serv_addr.sin_family = AF_INET;

	bcopy((char *)server->h_addr, (char *)&serv_addr.sin_addr.s_addr, server->h_length);

	serv_addr.sin_port = htons(portno);

	if (connect(sockfd, (struct sockaddr *) &serv_addr, sizeof(serv_addr)) < 0) {
		error("ERROR connecting");
	}

	printf("Please enter the message: ");

	bzero(buffer, 256);

	fgets(buffer, 255, stdin);

	len = strlen(buffer);

	for(i = 0; i < 4; i++){
		printf("0x%x\n", ((char*)&len)[i]);
	}

	len = htonl(len);
	
	for(i = 0; i < 4; i++){
		printf("0x%x\n", ((char*)&len)[i]);
	}

	write(sockfd, (void*)&len, 4);

	n = write(sockfd, buffer, strlen(buffer));

	if (n < 0){
		error("ERROR writing to socket");
	}

	close(sockfd);

	return 0;
}

#endif
