package com.example

import com.mfdeveloper.fcm.FCMClient
import com.mfdeveloper.fcm.AccessTokenType
import com.mfdeveloper.fcm.EnvironmentException

fun main() {
    println("Testing FCM library imports...")
    println()

    // Test 1: Verify classes can be instantiated
    try {
        val client = FCMClient("/nonexistent/path.json")
        println("✓ FCMClient class instantiated: ${client.javaClass.simpleName}")
    } catch (e: Exception) {
        println("✓ FCMClient class loaded (expected exception for missing file)")
    }

    // Test 2: Verify enum is accessible
    val tokenType = AccessTokenType.FIREBASE_ADMIN
    println("✓ AccessTokenType enum accessible: ${tokenType.value}")

    // Test 3: Verify HTTP API token type
    val httpTokenType = AccessTokenType.FCM_OAUTH_HTTP_API
    println("✓ AccessTokenType FCM_OAUTH_HTTP_API accessible: ${httpTokenType.value}")

    // Test 4: Verify exception class is accessible
    val exception = EnvironmentException("Test exception")
    println("✓ EnvironmentException class accessible: ${exception.message}")

    println()
    println("═══════════════════════════════════════════════════")
    println(" ✓ All library imports verified successfully!")
    println("═══════════════════════════════════════════════════")
}
