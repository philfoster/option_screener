include etrade.properties
AUTH_CLASS=com.discernative.GetAuthToken
RUN_CLASS=com.discernative.ITMScreener

JAR=dist/lib/EtradeTools.jar

THIRD_PARTY_JARS:=$(shell find lib -name "*.jar" -print | xargs echo | sed 's/ /:/g' )
CLASS_PATH=${THIRD_PARTY_JARS}:${JAR}

AUTH_TOKEN=auth_token.dat

.PHONY: run clean ${JAR}

all: clean run

run: ${AUTH_TOKEN}
	@ Running screener
	java -cp ${CLASS_PATH}:${JAR} ${RUN_CLASS}

${AUTH_TOKEN}: ${JAR}
	@echo "Generating Auth Token"
	java -cp ${CLASS_PATH}:${JAR} ${AUTH_CLASS} ${oauth_consumer_key} ${consumer_secret} ${environment}

clean:
	rm -f ${JAR}

veryclean:
	ant clean
	rm -f ${AUTH_TOKEN}

${JAR}:
	ant
