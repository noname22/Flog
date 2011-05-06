/*#pragma GCC system_header*/

#ifndef FLOG_H
#define FLOG_H

#ifdef __cplusplus
extern "C" {
#endif

#include <stdint.h>
#include <stdio.h>

typedef enum {
	Flog_SDebug1 = 1,
	Flog_SDebug2 = 2,
	Flog_SDebug3 = 4,
	Flog_SVerbose = 8,
	Flog_SInfo = 16,
	Flog_SWarning = 32,
	Flog_SError = 64,
	Flog_SFatal = 128
} Flog_Severity;

#define Flog_SAll 255
#define Flog_DefaultPort 13000

void Flog_Init(const char* applicationName);

int Flog_AddTargetFile(const char* filename, uint8_t filter);
void Flog_AddTargetStream(FILE* stream, uint8_t filter, int useAnsiColors);
int Flog_AddTargetServer(const char* address, uint16_t port, uint8_t filter);

void Flog_Log(const char* file, uint32_t lineNumber, Flog_Severity severity, const char* format, ...);

#define eprintf(...) fprintf (stderr, __VA_ARGS__)

#define FlogD1(...) Flog_Log(__FILE__, __LINE__, Flog_SDebug1, __VA_ARGS__)
#define FlogD2(...) Flog_Log(__FILE__, __LINE__, Flog_SDebug2, __VA_ARGS__)
#define FlogD3(...) Flog_Log(__FILE__, __LINE__, Flog_SDebug3, __VA_ARGS__)

#define FlogD FlogD3
#define FlogV(...) Flog_Log(__FILE__, __LINE__, Flog_SVerbose, __VA_ARGS__)
#define FlogI(...) Flog_Log(__FILE__, __LINE__, Flog_SInfo, __VA_ARGS__)
#define FlogW(...) Flog_Log(__FILE__, __LINE__, Flog_SWarning, __VA_ARGS__)
#define FlogE(...) Flog_Log(__FILE__, __LINE__, Flog_SError, __VA_ARGS__)
#define FlogF(...) Flog_Log(__FILE__, __LINE__, Flog_SFatal, __VA_ARGS__)

#ifdef __cplusplus
}
#endif

#endif
