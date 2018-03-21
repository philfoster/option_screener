include etrade.properties
MAIN_NAME=ITMScreener

JAR=dist/lib/EtradeTools.jar

THIRD_PARTY_JARS:=$(shell find lib -name "*.jar" -print | xargs echo | sed 's/ /:/g' )
CLASS_PATH=${THIRD_PARTY_JARS}:${JAR}

AUTH_TOKEN=auth_token.dat

.PHONY: run clean ${JAR}

all: clean run

run: ${AUTH_TOKEN}
	@ Running screener
	java -cp ${CLASS_PATH}:${JAR} com.discernative.ITMScreener

${AUTH_TOKEN}: ${JAR}
	@echo "Generating Auth Token"
	java -cp ${CLASS_PATH}:${JAR} com.discernative.GetAuthToken ${oauth_consumer_key} ${consumer_secret} ${environment}

clean:
	rm -f ${JAR}

veryclean:
	ant clean
	rm -f ${AUTH_TOKEN}

${JAR}:
	ant
