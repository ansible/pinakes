# Pinakes

Hi there! We're excited to have you as a contributor.

## Table of contents

- [Things to know prior to submitting code](#things-to-know-prior-to-submitting-code)
- [Setting up your development environment](#setting-up-your-development-environment)
- [What should I work on?](#what-should-i-work-on)
- [Submitting Pull Requests](#submitting-pull-requests)
- [Reporting Issues](#reporting-issues)

## Things to know prior to submitting code

- All code submissions are done through pull requests against the `devel` branch.
- Take care to make sure no merge commits are in the submission, and use `git rebase` vs `git merge` for this reason.
- We ask all of our community members and contributors to adhere to the [Ansible code of conduct](http://docs.ansible.com/ansible/latest/community/code_of_conduct.html). If you have questions, or need assistance, please reach out to our community team at [codeofconduct@ansible.com](mailto:codeofconduct@ansible.com)

## Setting up your development environment

Please view the [developer installation guide](./DEV_INSTALL.md)

## What should I work on?

Fixing bugs, adding translations, and updating the documentation are always appreciated, so reviewing the backlog of issues is always a good place to start.

> If you're planning to develop features or fixes for the UI, please review the [UI repository's contribution guide](https://github.com/ansible/pinakes-ui).

## Submitting Pull Requests

Fixes and Features for Pinakes will go through the Github pull request process. Submit your pull request (PR) against the `devel` branch.

Here are a few things you can do to help the visibility of your change, and increase the likelihood that it will be accepted:

- No issues when running linters/code checkers
- No issues from unit tests
- Write tests for new functionality, update/add tests for bug fixes
- Make the smallest change possible
- Write good commit messages. See [How to write a Git commit message](https://chris.beams.io/posts/git-commit/).

We like to keep our commit history clean, and will require resubmission of pull requests that contain merge commits. Use `git pull --rebase`, rather than
`git pull`, and `git rebase`, rather than `git merge`.

Sometimes it might take us a while to fully review your PR. We try to keep the `devel` branch in good working order, and so we review requests carefully. Please be patient.

All submitted PRs will have the linter and unit tests run against them via github actions, and the status reported in the PR.

## Reporting Issues

We welcome your feedback, and encourage you to file an issue when you run into a problem. But before opening a new issues, we ask that you please view our [Issues guide](./ISSUES.md).
