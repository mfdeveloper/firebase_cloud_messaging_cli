package com.mfdeveloper.fcm

import com.google.auth.oauth2.GoogleCredentials
import com.google.firebase.FirebaseApp
import com.google.firebase.FirebaseOptions
import com.google.firebase.messaging.FirebaseMessaging
import com.google.firebase.messaging.Message
import com.google.firebase.messaging.Notification
import com.google.gson.Gson
import java.io.File
import java.io.FileInputStream
import java.io.FileNotFoundException

/**
 * Firebase Cloud Messaging client for sending notifications.
 *
 * @param credentialsKeyFile Optional path to the service account JSON file.
 *                           If provided, takes precedence over GOOGLE_APPLICATION_CREDENTIALS.
 */
class FCMClient(private val credentialsKeyFile: String? = null) {
    
    private var credentialsInfo: Map<String, Any>? = null
    private var initialized = false
    
    /**
     * Get the path to the credentials file.
     *
     * Priority:
     * 1. `credentialsKeyFile` constructor argument
     * 2. `GOOGLE_APPLICATION_CREDENTIALS` environment variable
     *
     * @throws EnvironmentException if no credentials are provided
     * @throws FileNotFoundException if the credentials file doesn't exist
     */
    val credentialsPath: String
        get() {
            val credsPath = credentialsKeyFile 
                ?: System.getenv("GOOGLE_APPLICATION_CREDENTIALS")
                ?: throw EnvironmentException(
                    """No credentials provided. Please provide one of the following:
                    |  1. Use --credentials-key-file /path/to/service-account.json
                    |  2. Set environment variable: export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
                    """.trimMargin()
                )
            
            if (!File(credsPath).exists()) {
                throw FileNotFoundException("Credentials file not found: $credsPath")
            }
            
            return credsPath
        }
    
    /**
     * Load and return the service account credentials info.
     */
    @Suppress("UNCHECKED_CAST")
    fun getCredentialsInfo(): Map<String, Any>? {
        if (credentialsInfo == null) {
            val file = File(credentialsPath)
            credentialsInfo = Gson().fromJson(file.readText(), Map::class.java) as Map<String, Any>
        }
        return credentialsInfo
    }
    
    /**
     * Get the project ID from credentials.
     */
    val projectId: String
        get() = getCredentialsInfo()?.get("project_id")?.toString() ?: ""
    
    /**
     * Get the service account email from credentials.
     */
    val serviceAccountEmail: String
        get() = getCredentialsInfo()?.get("client_email")?.toString() ?: ""
    
    /**
     * Initialize the Firebase Admin SDK.
     *
     * If credentialsKeyFile was provided, it sets the environment variable
     * so that Google Application Default Credentials (ADC) can find it.
     */
    fun initialize() {
        if (!initialized && FirebaseApp.getApps().isEmpty()) {
            // If constructor argument was provided, set the environment variable for ADC
            credentialsKeyFile?.let {
                System.setProperty("GOOGLE_APPLICATION_CREDENTIALS", it)
            }
            
            val credentials = GoogleCredentials.fromStream(FileInputStream(credentialsPath))
                .createScoped(listOf("https://www.googleapis.com/auth/firebase.messaging"))
            
            val options = FirebaseOptions.builder()
                .setCredentials(credentials)
                .setProjectId(projectId)
                .build()
            
            FirebaseApp.initializeApp(options)
            initialized = true
        }
    }
    
    /**
     * Get the current access token from Firebase Admin SDK.
     */
    fun getAccessToken(): String {
        initialize()
        val credentials = GoogleCredentials.fromStream(FileInputStream(credentialsPath))
            .createScoped(listOf("https://www.googleapis.com/auth/firebase.messaging"))
        credentials.refreshIfExpired()
        return credentials.accessToken?.tokenValue ?: ""
    }
    
    /**
     * Get the current Google OAuth2 access token for using with FCM HTTP API.
     */
    fun getAccessTokenHttpApi(): String {
        initialize()
        val credentials = GoogleCredentials.fromStream(FileInputStream(credentialsPath))
            .createScoped(listOf(
                "https://www.googleapis.com/auth/firebase.messaging",
                "https://www.googleapis.com/auth/cloud-platform"
            ))
        credentials.refreshIfExpired()
        return credentials.accessToken?.tokenValue ?: ""
    }
    
    /**
     * Display service account information and access token.
     */
    fun showInfo(accessTokenType: AccessTokenType) {
        println()
        println("=".repeat(60))
        println("Firebase Service Account Information")
        println("=".repeat(60))
        println("  PROJECT_ID:            $projectId")
        println("  SERVICE_ACCOUNT_EMAIL: $serviceAccountEmail")
        println("  CREDENTIALS_FILE:      $credentialsPath")
        println("=".repeat(60))
        
        try {
            val accessToken = when (accessTokenType) {
                AccessTokenType.FCM_OAUTH_HTTP_API -> {
                    val token = getAccessTokenHttpApi()
                    println()
                    println("  ACCESS_TOKEN (first 50 chars): ${token.take(50)}...")
                    token
                }
                AccessTokenType.FIREBASE_ADMIN -> getAccessToken()
            }
            println("  ACCESS_TOKEN (full):\n$accessToken")
        } catch (e: Exception) {
            println()
            println("  Error retrieving access token: ${e.message}")
        }
        
        println("=".repeat(60))
        println()
    }
    
    /**
     * Send an FCM notification to a specific device.
     *
     * @param fcmToken The FCM registration token of the target device
     * @param title Notification title
     * @param body Notification body
     * @param data Optional custom data payload
     * @param imageUrl Optional image URL for the notification
     * @param dryRun If true, validates message without sending
     * @return The message ID from FCM
     */
    fun sendNotification(
        fcmToken: String,
        title: String,
        body: String,
        data: Map<String, String>? = null,
        imageUrl: String? = null,
        dryRun: Boolean = false
    ): String {
        initialize()
        
        val notificationBuilder = Notification.builder()
            .setTitle(title)
            .setBody(body)
        
        imageUrl?.let { notificationBuilder.setImage(it) }
        
        val messageBuilder = Message.builder()
            .setNotification(notificationBuilder.build())
            .setToken(fcmToken)
        
        data?.let { messageBuilder.putAllData(it) }
        
        return FirebaseMessaging.getInstance().send(messageBuilder.build(), dryRun)
    }
    
    /**
     * Send a data-only FCM message to a specific device.
     *
     * @param fcmToken The FCM registration token of the target device
     * @param data Custom data payload (map with string keys and values)
     * @param dryRun If true, validates message without sending
     * @return The message ID from FCM
     */
    fun sendDataMessage(
        fcmToken: String,
        data: Map<String, Any>,
        dryRun: Boolean = false
    ): String {
        initialize()
        
        // Ensure all data values are strings (FCM requirement)
        val stringData = data.mapValues { it.value.toString() }
        
        val message = Message.builder()
            .putAllData(stringData)
            .setToken(fcmToken)
            .build()
        
        return FirebaseMessaging.getInstance().send(message, dryRun)
    }
}

/**
 * Exception thrown when environment configuration is missing.
 */
class EnvironmentException(message: String) : Exception(message)
