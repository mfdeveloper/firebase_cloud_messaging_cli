package com.mfdeveloper.fcm

import com.github.ajalt.clikt.core.CliktCommand
import com.github.ajalt.clikt.core.ProgramResult
import com.github.ajalt.clikt.parameters.options.default
import com.github.ajalt.clikt.parameters.options.flag
import com.github.ajalt.clikt.parameters.options.option
import com.github.ajalt.clikt.parameters.options.versionOption
import com.google.firebase.messaging.FirebaseMessagingException
import com.google.gson.Gson
import com.google.gson.JsonSyntaxException

/**
 * Command-line interface handler for FCM operations.
 */
class CLIHandler : CliktCommand(
    name = "fcm-send",
    help = "Send Firebase Cloud Messaging notifications"
) {
    
    private val credentialsKeyFile: String? by option(
        "--credentials-key-file",
        metavar = "PATH",
        help = "Path to Firebase service account JSON file (takes precedence over GOOGLE_APPLICATION_CREDENTIALS)"
    )
    
    private val info: Boolean by option(
        "--info",
        help = "Display service account info and Firebase Admin SDK access token"
    ).flag()
    
    private val accessToken: Boolean by option(
        "--access-token",
        help = "Display service account info and Firebase Admin SDK access token"
    ).flag()
    
    private val infoHttp: Boolean by option(
        "--info-http",
        help = "Display service account info and Google OAuth2 access token for using with FCM HTTP API"
    ).flag()
    
    private val accessTokenHttp: Boolean by option(
        "--access-token-http",
        help = "Display service account info and Google OAuth2 access token for using with FCM HTTP API"
    ).flag()
    
    private val token: String? by option(
        "--token",
        metavar = "FCM_TOKEN",
        help = "FCM registration token of the target device"
    )
    
    private val title: String? by option(
        "--title",
        help = "Notification title"
    )
    
    private val body: String? by option(
        "--body",
        help = "Notification body"
    )
    
    private val data: String? by option(
        "--data",
        metavar = "JSON",
        help = "Custom data payload as JSON string (e.g., '{\"key\": \"value\"}')"
    )
    
    private val dataOnly: String? by option(
        "--data-only",
        metavar = "JSON",
        help = "Send data-only message (no notification) with JSON payload"
    )
    
    private val image: String? by option(
        "--image",
        metavar = "URL",
        help = "Image URL for the notification"
    )
    
    private val dryRun: Boolean by option(
        "--dry-run",
        help = "Validate the message without actually sending it"
    ).flag()
    
    init {
        versionOption(VERSION)
    }
    
    lateinit var client: FCMClient
    
    override fun run() {
        client = FCMClient(credentialsKeyFile)
        
        when {
            // Show info mode with Firebase Admin SDK access token
            info || accessToken -> handleInfo()
            
            // Show info mode with Google OAuth2 (HTTP) access token
            infoHttp || accessTokenHttp -> handleInfo(AccessTokenType.FCM_OAUTH_HTTP_API)
            
            // Data-only message mode
            dataOnly != null -> {
                if (token == null) {
                    echo("Error: --token is required for sending messages", err = true)
                    throw ProgramResult(2)
                }
                handleDataOnly()
            }
            
            // Regular notification mode
            token != null -> {
                if (title == null || body == null) {
                    echo("Error: --title and --body are required for notifications", err = true)
                    throw ProgramResult(2)
                }
                handleNotification()
            }
            
            // No valid action specified - show help
            else -> {
                echo(getFormattedHelp())
            }
        }
    }
    
    /**
     * Handle the --info command.
     */
    fun handleInfo(accessTokenType: AccessTokenType = AccessTokenType.FIREBASE_ADMIN) {
        try {
            client.showInfo(accessTokenType)
        } catch (e: EnvironmentException) {
            echo("Error: ${e.message}", err = true)
            throw ProgramResult(1)
        } catch (e: java.io.FileNotFoundException) {
            echo("Error: ${e.message}", err = true)
            throw ProgramResult(1)
        }
    }
    
    /**
     * Handle the --data-only command.
     */
    @Suppress("UNCHECKED_CAST")
    fun handleDataOnly() {
        val parsedData: Map<String, Any>
        try {
            parsedData = Gson().fromJson(dataOnly, Map::class.java) as Map<String, Any>
        } catch (e: JsonSyntaxException) {
            echo("Error: Invalid JSON in --data-only: ${e.message}", err = true)
            throw ProgramResult(1)
        }
        
        try {
            val response = client.sendDataMessage(token!!, parsedData, dryRun)
            if (dryRun) {
                echo()
                echo("✓ Dry run successful! Data message is valid.")
                echo("  Message ID (dry run): $response")
            } else {
                echo()
                echo("✓ Data message sent successfully!")
                echo("  Message ID: $response")
            }
        } catch (e: Exception) {
            echo()
            echo("✗ Error sending data message: ${e.message}", err = true)
            throw ProgramResult(1)
        }
    }
    
    /**
     * Handle the notification command.
     */
    @Suppress("UNCHECKED_CAST")
    fun handleNotification() {
        var parsedData: Map<String, String>? = null
        
        if (data != null) {
            try {
                val rawData = Gson().fromJson(data, Map::class.java) as Map<String, Any>
                // Ensure all values are strings
                parsedData = rawData.mapValues { it.value.toString() }
            } catch (e: JsonSyntaxException) {
                echo("Error: Invalid JSON in --data: ${e.message}", err = true)
                throw ProgramResult(1)
            }
        }
        
        try {
            val response = client.sendNotification(
                fcmToken = token!!,
                title = title!!,
                body = body!!,
                data = parsedData,
                imageUrl = image,
                dryRun = dryRun
            )
            
            if (dryRun) {
                echo()
                echo("✓ Dry run successful! Message is valid.")
                echo("  Message ID (dry run): $response")
            } else {
                echo()
                echo("✓ Notification sent successfully!")
                echo("  Message ID: $response")
            }
        } catch (e: FirebaseMessagingException) {
            echo()
            when (e.messagingErrorCode?.name) {
                "UNREGISTERED" -> {
                    echo("✗ Error: The FCM token is not registered (device may have uninstalled the app)", err = true)
                }
                "SENDER_ID_MISMATCH" -> {
                    echo("✗ Error: The FCM token does not match the sender ID (wrong project?)", err = true)
                }
                else -> {
                    echo("✗ Error sending notification: ${e.message}", err = true)
                }
            }
            throw ProgramResult(1)
        } catch (e: Exception) {
            echo()
            echo("✗ Error sending notification: ${e.message}", err = true)
            throw ProgramResult(1)
        }
    }
    
    companion object {
        const val VERSION = "0.1.1"
    }
}
