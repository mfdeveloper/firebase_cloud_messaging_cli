package com.mfdeveloper.fcm

/**
 * Type of access token to retrieve.
 */
enum class AccessTokenType(val value: String) {
    /**
     * Firebase Admin SDK access token.
     */
    FIREBASE_ADMIN("firebase_admin"),
    
    /**
     * Google OAuth2 access token for FCM HTTP API.
     */
    FCM_OAUTH_HTTP_API("fcm_http_api")
}
