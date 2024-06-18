FROM harbor2.vantage6.ai/infrastructure/algorithm-ohdsi-base:${BASE}

ARG BASE=4.5
ARG TAG=latest
ARG PKG_NAME="v6-kaplan-meier-py"

LABEL version=${TAG}
LABEL maintainer="F.C. Martin <f.martin@iknl.nl>"
LABEL maintainer="A.J. van Gestel <a.vangestel@iknl.nl>"

# This will install your algorithm into this image.
COPY . /app
RUN pip install /app

# This will run your algorithm when the Docker container is started. The
# wrapper takes care of the IO handling (communication between node and
# algorithm). You dont need to change anything here.
ENV PKG_NAME=${PKG_NAME}
CMD python -c "from vantage6.algorithm.tools.wrap import wrap_algorithm; wrap_algorithm()"
