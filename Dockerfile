ARG PYTHON_BASE_IMAGE=quay.io/ansible/python-base:latest
ARG PYTHON_BUILDER_IMAGE=quay.io/ansible/python-builder:latest
ARG ZUUL_SIBLINGS=""

FROM $PYTHON_BUILDER_IMAGE as builder
# =============================================================================
ARG ZUUL_SIBLINGS

COPY . /tmp/src
# NOTE(pabelanger): For downstream builds, we compile everything from source
# over using existing wheels. Do this upstream too so we can better catch
# issues.
ENV PIP_OPTS=--no-build-isolation
RUN assemble

FROM $PYTHON_BASE_IMAGE
# =============================================================================

COPY --from=builder /output/ /output
RUN /output/install-from-bindep \
  && rm -rf /output
