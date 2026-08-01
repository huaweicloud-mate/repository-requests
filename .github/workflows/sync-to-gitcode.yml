name: Sync to GitCode

on:
  push:
    branches: ["*"]
  delete:

jobs:
  sync:
    uses: huaweicloud-mate/.github/.github/workflows/sync-to-gitcode.yml@main
    secrets:
      GITCODE_USERNAME: ${{ secrets.GITCODE_USERNAME }}
      GITCODE_TOKEN: ${{ secrets.GITCODE_TOKEN }}