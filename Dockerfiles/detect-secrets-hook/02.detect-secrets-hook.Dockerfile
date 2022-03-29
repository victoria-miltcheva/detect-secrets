FROM git-defenders/base/cli

RUN git config --system core.safecrlf false
ENTRYPOINT [ "detect-secrets-hook" ]
