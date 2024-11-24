FROM python:3.10-bullseye

RUN apt-get update && apt-get install -y curl

CMD curl -v https://efiling.drcor.mcit.gov.cy/DrcorPublic/SearchForm.aspx?sc=0
