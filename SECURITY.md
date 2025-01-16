# Security Policy

## Supported Versions

As we have not published any versions of PalTrack yet, the only supported version is `main`.
We will accept all reports of security vulnerabilities, no matter how trivial, and ask that they are
disclosed responsibly (see below).

## Reporting a Vulnerability

Send all reports securely to `contact@paltrack.dev`.

We highly recommend sending emails using GPG. 
All of our maintainers who can respond to security inquiries have keys published at https://keys.openpgp.org. 
Further, you should demand that all of our responses are encrypted with your GPG public key (please provide it on first contact)

Follow these instructions to determine which GPG key to use:

- **If it is before 19 July 2025**: use key `7786034BD52149F51B0A2A14B1122F04E962DDC5` registered to `Amy Parker <amy@amyip.net>`.
- Otherwise, check for another key verified to the **amy@amyip.net** email address **on keys.openpgp.org ONLY** and which has been signed by Amy's prior key. If not, continue below.
- **If it is before 5 January 2026**: use key `8ABA6EC91A67EA641772E6D7A90568CBA63816BE` registered to `Amir Valiulla <amirvaliulla32@gmail.com>`.
- Otherwise, use key `C286BF1F49818C7FAF5B403A184751B4E8F88000` registered to `PalTrack Server <contact@paltrack.dev>`.
  - Communications using this key are more secure than those without it, but cannot be guaranteed to be fully confidential. 
    A much better option is to directly contact a maintainer and inform them that their GPG key has expired and has not been renewed.
    If communicating using this method, do NOT provide any personally identifiable information or use an institutional email address.

## Penetration Testing

**DO NOT attempt to penetrate live PalTrack instances without the written consent of the owner.**
We **DO NOT** grant blanket consent to test on our PalTrack instance. If you'd like to help us
out with penetration testing, reach out to us at `contact@paltrack.dev`.
