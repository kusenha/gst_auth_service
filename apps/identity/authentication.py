from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication


class CutoffAwareJWTAuthentication(JWTAuthentication):
    """Rejects any access token issued before the user's last logout.

    LogoutView stamps UserProfile.tokensInvalidBefore with the logout time.
    A JWT's own expiry can't be revoked once signed, so this is the actual
    enforcement point: every authenticated request compares the token's
    `iat` claim against that cutoff and rejects stale tokens outright,
    regardless of which app/tab is still holding one.
    """

    def get_user(self, validated_token):
        user = super().get_user(validated_token)
        profile = getattr(user, "profile", None)
        cutoff = getattr(profile, "tokensInvalidBefore", None)
        if cutoff is None:
            return user

        issued_at = validated_token.get("iat")
        if issued_at is None:
            return user

        # JWT `iat` is whole-second precision; floor the cutoff to match, or
        # a token minted in the same second as the logout (a near-instant
        # re-login) would be wrongly rejected by its own sub-second fraction.
        if issued_at < int(cutoff.timestamp()):
            raise AuthenticationFailed("Token has been invalidated by a logout.", code="token_invalidated")

        return user
