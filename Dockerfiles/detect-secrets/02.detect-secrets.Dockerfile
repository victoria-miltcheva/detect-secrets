FROM git-defenders/base/cli
ENTRYPOINT [ "detect-secrets" ]
CMD [ "scan", "/code" ]
