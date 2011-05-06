#include <stdio.h>
#include <flog.h>
#include <stdlib.h>

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
	
	if( !Flog_AddTargetServer("192.168.10.34", Flog_DefaultPort, Flog_SAll) ){
		printf("couldn't connect to server\n");
		return 1;
	}

	std::string testString = "value";

	FlogExpD1(testString);

	FlogD1("debug level " << 1);
	FlogD2("debug level " << 2);
	FlogD3("debug level " << 3);
	FlogD("debug default level");
	FlogV("verbose");
	FlogI("info");
	FlogW("warning");
	FlogE("error");
	FlogF("fatal error");

	return 0;
}
