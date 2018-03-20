MAIN_NAME=ITMScreener
CLEAN_TARGETS=*.class

COMPILE_TARGETS=ITMScreener.class EtradeTools.class GetAuthToken.class AuthToken.class OptionChainQuote.class CallOptionQuote.class PutOptionQuote.class

JAVA_OPTS=-Xlint:deprecation

#CLASS_PATH=./jars:.

CLASS_PATH=jars/commons-codec-1.3.jar:jars/commons-httpclient-3.1.jar:jars/commons-httpclient-contrib-ssl-3.1.jar:jars/commons-lang-2.4.jar:jars/commons-logging.jar:jars/etws-accounts-sdk-1.0.jar:jars/etws-common-connections-1.0.jar:jars/etws-market-sdk-1.0.jar:jars/etws-oauth-sdk-1.0.jar:jars/etws-order-sdk-1.0.jar:jars/xstream-1.3.1.jar:jars/log4j-1.2.15.jar:.

.PHONY: run auth

all: clean ${COMPILE_TARGETS} 

auth:
	@java -cp ${CLASS_PATH} GetAuthToken

run: ${COMPILE_TARGETS}
	@java -cp ${CLASS_PATH} ${MAIN_NAME}
	
ITMScreener.class: EtradeTools.class
	@echo compiling $@
	javac ${JAVA_OPTS} -cp ${CLASS_PATH} ITMScreener.java

GetAuthToken.class: EtradeTools.class
	@echo compiling $@
	javac ${JAVA_OPTS} -cp ${CLASS_PATH} GetAuthToken.java

EtradeTools.class:
	@echo compiling $@
	javac ${JAVA_OPTS} -cp ${CLASS_PATH} EtradeTools.java

AuthToken.class:
	@echo compiling $@
	javac ${JAVA_OPTS} -cp ${CLASS_PATH} AuthToken.java

OptionChainQuote.class:
	@echo compiling $@
	javac ${JAVA_OPTS} -cp ${CLASS_PATH} OptionChainQuote.java

CallOptionQuote.class:
	@echo compiling $@
	javac ${JAVA_OPTS} -cp ${CLASS_PATH} CallOptionQuote.java

PutOptionQuote.class:
	@echo compiling $@
	javac ${JAVA_OPTS} -cp ${CLASS_PATH} PutOptionQuote.java

clean:	
	rm -rf ${CLEAN_TARGETS}
