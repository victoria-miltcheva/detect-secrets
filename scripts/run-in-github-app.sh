#!/bin/bash -e
# Enviroment varibles
# REPO_SLUG
# GITHUB_APP_ID
# GITHUB_APP_KEY
# REPO_INSTALL_ID
# COMMIT_HASH
# Optional CHECK_RUN_ID if a queued check run was run

BASEDIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
# shellcheck source=/dev/null
source "$BASEDIR/lib.sh"
CODE_DIR=$(mktemp -d)
GITHUB_ADDR=github.ibm.com
GITHUB_REPO_URL=https://$GITHUB_ADDR/api/v3/repos/$REPO_SLUG
CHECK_NAME=whitewater-detect-secrets

if [ -n "$DEPLOY_LEVEL" ] && [ "$DEPLOY_LEVEL" != "production" ]
then
  CHECK_NAME="whitewater-detect-secrets-$DEPLOY_LEVEL"
fi

if [ -n "$APP_ID" ]
then
  GITHUB_APP_ID=$APP_ID
fi

GITHUB_CURL() {
    local REPO_URL=$1
    shift
    curl \
        -H "Authorization: token $ACCESS_TOKEN" \
        -H "Accept: application/vnd.github.antiope-preview+json" \
        $@ \
        "$GITHUB_REPO_URL/$REPO_URL"
}

echo "Getting access token"
ACCESS_TOKEN=$(GET_INSTALLATION_TOKEN "$GITHUB_APP_ID" "$GITHUB_APP_KEY" "$REPO_INSTALL_ID")

GET_CHECK_RUN() {
    GITHUB_CURL "commits/$COMMIT_HASH/check-runs?check_name=$CHECK_NAME" -s
}

echo "Seeing check run '$CHECK_RUN_ID' (will be blank if no check run)"

# trying to find a check run which is queued otherwise it will make a new one
if [ -z "$CHECK_RUN_ID" ]
then
  CHECK_RUN=$(GET_CHECK_RUN)

  CHECK_RUN_STATUS=$(echo "$CHECK_RUN"| jq -r '.check_runs[0].status')
  if [ "$CHECK_RUN_STATUS" = "queued" ]
  then
    CHECK_RUN_ID=$(echo "$CHECK_RUN" | jq -r '.check_runs[0].id')
  fi
fi

if [ -z "$CHECK_RUN_ID" ]
then
    echo "Making new check_run"
    jq -n "{
        head_sha: \"$COMMIT_HASH\",
        name: \"$CHECK_NAME\",
        status: \"in_progress\",
        started_at: now | todateiso8601
    }" | GITHUB_CURL check-runs -fs -X POST -d @- > /dev/null
    echo "Made check run, now getting id"
    CHECK_RUN_ID=$(GET_CHECK_RUN | jq -r '.check_runs[0].id')
    if [ "$CHECK_RUN_ID" = "null" ]
    then
        echo "Error making check run exiting"
        exit 1
    fi
    echo "Got id '$CHECK_RUN_ID'"
else
    echo "Updating check run"
    jq -n "{
        status: \"in_progress\",
        started_at: now | todateiso8601
    }" | GITHUB_CURL "check-runs/$CHECK_RUN_ID" -fs -X PATCH -d @- > /dev/null
fi

echo "Cloning repo"
git clone --depth 50 --no-single-branch "https://x-access-token:$ACCESS_TOKEN@$GITHUB_ADDR/$REPO_SLUG.git" "$CODE_DIR"
cd "$CODE_DIR"

# only support commit at the tip of the pull request
GIT_BRANCH=$(git ls-remote | grep -m1 "^$COMMIT_HASH" | cut -f2 || true)

if [ -n "$GIT_BRANCH" ]
then
  git fetch origin "$GIT_BRANCH"
  git checkout -qf FETCH_HEAD
else
  if git checkout "$COMMIT_HASH"; then
    echo "Find $COMMIT_HASH"
  else
    echo -n "Can not find $COMMIT_HASH with shallow clone. "
    echo "We will fetch all refs."
    git fetch --unshallow origin || git fetch origin
    git checkout "$COMMIT_HASH"
  fi
fi

echo "Running scan"
RET_VAL=0
CODE=$CODE_DIR "$BASEDIR/../run-scan.sh" || RET_VAL=1
if [ "$RET_VAL" -eq 0 ]
then
    echo "Scan successful"
    CONCLUSION="success"
    OUTPUT_TITLE="No secrets identified"
    OUTPUT_SUMMARY="We did not find any secrets in the code, but the scan is"
    OUTPUT_SUMMARY="$OUTPUT_SUMMARY not perfect. You should always review the"
    OUTPUT_SUMMARY="$OUTPUT_SUMMARY code to make sure no secrets are added."
else
    echo "Scan failed"
    CONCLUSION="failure"
    OUTPUT_TITLE="Potential secrets identified"
    read -r -d '' OUTPUT_SUMMARY << EOF
Detect Secrets has identified potential secrets in the code.  Review each finding and determine if it is a secret or not a secret.

If it is a secret follow the remediation steps in [ Managing Credentials ]( https://pages.github.ibm.com/Whitewater/fieldguide/practices/managing-credentials).

If it is not a secret you can indicate this in the code with a comment \`# pragma: whitelist secret\` or if you have a large number of results to whitelist we recommend you create a secrets baseline following the steps in the [getting started guide](https://w3.ibm.com/w3publisher/detect-secrets/getting-started).
EOF
fi

echo "Refreshing access token"
ACCESS_TOKEN=$(GET_INSTALLATION_TOKEN "$GITHUB_APP_ID" "$GITHUB_APP_KEY" "$REPO_INSTALL_ID")

echo "Updating check run"
if [ "$DEBUG" = "yes" ]
then
  cat "$CODE_DIR/.secrets.baseline"
fi

# todo update to latest when GHE update. 2.14 is on a different API version as github.com
jq "{
    completed_at: now | todateiso8601,
    conclusion: \"$CONCLUSION\",
    status: \"completed\",
    output: {
        title: \"$OUTPUT_TITLE\",
        summary: \"$OUTPUT_SUMMARY\",
        annotations: [
            .results | to_entries | .[] | { filename: .key } + .value[] |
            select( if .is_secret == null then true else .is_secret end ) | {
                filename: .filename,
                blob_href: ( \"https://github.ibm.com/$REPO_SLUG/blob/$COMMIT_HASH/\" + .filename ),
                start_line: .line_number,
                end_line: .line_number,
                message: ( \"Potential secret identified by \" + .type + \" refer to the [guide](https://w3.ibm.com/w3publisher/detect-secrets) for guidance if needed\" ),
                warning_level: \"failure\"
            }
        ] | [limit(48;.[])]
    }
}" < "$CODE_DIR/.secrets.baseline" | GITHUB_CURL "check-runs/$CHECK_RUN_ID" -fs -X PATCH -d @- > /dev/null

## code for the latest github.com
# cat $CODE_DIR/.secrets.baseline | jq "{
#     completed_at: now | todateiso8601,
#     conclusion: \"$CONCLUSION\",
#     status: \"completed\",
#     output: {
#         title: \"$OUTPUT_TITLE\",
#         summary: \"$OUTPUT_SUMMARY\",
#         annotations: [
#             .results | to_entries | .[] | { filename: .key } + .value[] |
#             select( if .is_secret == null then true else .is_secret end ) | {
#                 path: .filename,
#                 start_line: .line_number,
#                 end_line: .line_number,
#                 message: .type,
#                 annotation_level: \"failure\"
#             }
#         ]
#     }
# }" | GITHUB_CURL check-runs/$CHECK_RUN_ID -f -X PATCH -d @-

rm -rf "$CODE_DIR"
