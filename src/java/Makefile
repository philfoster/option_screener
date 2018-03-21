MAIN_NAME=ITMScreener

JAR=dist/lib/EtradeTools.jar

THIRD_PARTY_JARS:=$(shell find lib -name "*.jar" -print | xargs echo | sed 's/ /:/g' )
CLASS_PATH=${THIRD_PARTY_JARS}:${JAR}

.PHONY: run auth clean

all: clean run

run: ${JAR}
	java -cp ${CLASS_PATH}:${JAR} ITMScreener
	
auth: ${JAR}
	java -cp ${CLASS_PATH}:${JAR} GetAuthToken

clean:
	rm -f ${JAR}

${JAR}:
	ant
