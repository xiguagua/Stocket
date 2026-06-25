#!/bin/bash
# Get the latest two tags
TAGS=$(git tag -l --sort=-v:refname | head -n 2)
TAG_COUNT=$(echo "$TAGS" | wc -l)

if [ "$TAG_COUNT" -lt 2 ]; then
  # If less than 2 tags, get all commits up to the latest tag, or just last 20 if no tags
  LATEST_TAG=$(echo "$TAGS" | head -n 1)
  if [ -z "$LATEST_TAG" ]; then
    git log -n 20 --oneline
  else
    git log "$LATEST_TAG" -n 20 --oneline
  fi
else
  TAG1=$(echo "$TAGS" | sed -n '1p')
  TAG2=$(echo "$TAGS" | sed -n '2p')
  echo "Comparing $TAG2..$TAG1"
  git log "$TAG2..$TAG1" --oneline
fi
