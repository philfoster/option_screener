include etrade.properties
AUTH_CLASS=com.discernative.etradetools.GetAuthToken
RUN_CLASS=com.discernative.etradetools.ITMScreener

JAR=dist/lib/EtradeTools.jar

THIRD_PARTY_JARS:=$(shell find lib -name "*.jar" -print | xargs echo | sed 's/ /:/g' )
CLASS_PATH=${THIRD_PARTY_JARS}:${JAR}

SCREENER_PROPERTIES=screener.properties

AUTH_TOKEN=auth_token.dat

.PHONY: run clean ${JAR}

all: clean run

run: ${AUTH_TOKEN} ${JAR}
	@echo Running screener
	java -cp ${CLASS_PATH}:${JAR} ${RUN_CLASS} ${SCREENER_PROPERTIES}

${AUTH_TOKEN}: 
	@echo "Generating Auth Token"
	java -cp ${CLASS_PATH}:${JAR} ${AUTH_CLASS} etrade.properties

clean:
	rm -f ${JAR}

veryclean:
	ant clean
	rm -f ${AUTH_TOKEN}

${JAR}:
	ant
