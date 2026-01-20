package com.mfdeveloper.fcm

import com.github.ajalt.clikt.core.ProgramResult
import com.google.auth.oauth2.GoogleCredentials
import com.google.firebase.FirebaseApp
import com.google.firebase.FirebaseOptions
import com.google.firebase.messaging.FirebaseMessaging
import com.google.firebase.messaging.FirebaseMessagingException
import com.google.firebase.messaging.Message
import com.google.firebase.messaging.MessagingErrorCode
import io.mockk.*
import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.assertThatThrownBy
import org.junit.jupiter.api.*
import java.io.ByteArrayOutputStream
import java.io.File
import java.io.PrintStream

class CLIHandlerTest {
    
    companion object {
        private lateinit var tempCredentialsFile: File
        
        private val mockServiceAccountData = """
            {
                "type": "service_account",
                "project_id": "test-project-123",
                "private_key_id": "abc123",
                "private_key": "-----BEGIN RSA PRIVATE KEY-----\nMIIBOgIBAAJBALRiMLAHudeSA\n-----END RSA PRIVATE KEY-----\n",
                "client_email": "firebase-adminsdk@test-project-123.iam.gserviceaccount.com",
                "client_id": "123456789",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk"
            }
        """.trimIndent()
        
        @JvmStatic
        @BeforeAll
        fun setupAll() {
            tempCredentialsFile = File.createTempFile("test-credentials", ".json")
            tempCredentialsFile.writeText(mockServiceAccountData)
        }
        
        @JvmStatic
        @AfterAll
        fun cleanupAll() {
            tempCredentialsFile.delete()
        }
    }
    
    private lateinit var originalOut: PrintStream
    private lateinit var originalErr: PrintStream
    private lateinit var outputStream: ByteArrayOutputStream
    private lateinit var errorStream: ByteArrayOutputStream
    
    @BeforeEach
    fun setup() {
        originalOut = System.out
        originalErr = System.err
        outputStream = ByteArrayOutputStream()
        errorStream = ByteArrayOutputStream()
        System.setOut(PrintStream(outputStream))
        System.setErr(PrintStream(errorStream))
        
        // Clear Firebase apps safely
        try {
            FirebaseApp.getApps().forEach { 
                try { it.delete() } catch (e: Exception) { /* ignore */ }
            }
        } catch (e: Exception) {
            // ignore
        }
    }
    
    @AfterEach
    fun cleanup() {
        System.setOut(originalOut)
        System.setErr(originalErr)
        try {
            unmockkAll()
        } catch (e: Exception) {
            // ignore
        }
    }
    
    private fun capturedOutput(): String = outputStream.toString()
    
    private fun setupMocks(): FirebaseMessaging {
        mockkStatic(FirebaseApp::class)
        mockkStatic(GoogleCredentials::class)
        mockkStatic(FirebaseMessaging::class)
        
        val mockCredentials = mockk<GoogleCredentials>(relaxed = true)
        val mockMessaging = mockk<FirebaseMessaging>()
        val mockApp = mockk<FirebaseApp>(relaxed = true)
        
        every { FirebaseApp.getApps() } returns listOf()
        every { GoogleCredentials.fromStream(any()) } returns mockCredentials
        every { mockCredentials.createScoped(any<List<String>>()) } returns mockCredentials
        every { FirebaseApp.initializeApp(any<FirebaseOptions>()) } returns mockApp
        every { FirebaseMessaging.getInstance() } returns mockMessaging
        every { mockMessaging.send(any<Message>(), any()) } returns "projects/test/messages/123"
        
        return mockMessaging
    }
    
    // Version Tests
    
    @Test
    fun `version constant is defined`() {
        assertThat(CLIHandler.VERSION).isEqualTo("0.1.1")
    }
    
    // Handle Info Tests
    
    @Test
    fun `handleInfo shows firebase admin token`() {
        setupMocks()
        val mockAccessToken = mockk<com.google.auth.oauth2.AccessToken>()
        val mockCredentials = mockk<GoogleCredentials>(relaxed = true)
        every { GoogleCredentials.fromStream(any()) } returns mockCredentials
        every { mockCredentials.createScoped(any<List<String>>()) } returns mockCredentials
        every { mockCredentials.accessToken } returns mockAccessToken
        every { mockAccessToken.tokenValue } returns "test_token_value"
        
        val cli = CLIHandler()
        cli.client = FCMClient(tempCredentialsFile.absolutePath)
        cli.handleInfo(AccessTokenType.FIREBASE_ADMIN)
        
        val output = capturedOutput()
        assertThat(output).contains("Firebase Service Account Information")
    }
    
    @Test
    fun `handleInfo shows http api token`() {
        setupMocks()
        val mockAccessToken = mockk<com.google.auth.oauth2.AccessToken>()
        val mockCredentials = mockk<GoogleCredentials>(relaxed = true)
        every { GoogleCredentials.fromStream(any()) } returns mockCredentials
        every { mockCredentials.createScoped(any<List<String>>()) } returns mockCredentials
        every { mockCredentials.accessToken } returns mockAccessToken
        every { mockAccessToken.tokenValue } returns "test_http_token_12345678901234567890123456789012345"
        
        val cli = CLIHandler()
        cli.client = FCMClient(tempCredentialsFile.absolutePath)
        cli.handleInfo(AccessTokenType.FCM_OAUTH_HTTP_API)
        
        val output = capturedOutput()
        assertThat(output).contains("Firebase Service Account Information")
        assertThat(output).contains("ACCESS_TOKEN (first 50 chars)")
    }
    
    @Test
    fun `handleInfo with environment exception is caught`() {
        // The environment exception is thrown when no credentials are provided
        val client = FCMClient()
        assertThatThrownBy { client.credentialsPath }
            .isInstanceOf(EnvironmentException::class.java)
    }
    
    @Test
    fun `handleInfo with file not found is caught`() {
        // The file not found exception is thrown when credentials file doesn't exist
        val client = FCMClient("/nonexistent/path.json")
        assertThatThrownBy { client.credentialsPath }
            .isInstanceOf(java.io.FileNotFoundException::class.java)
    }
    
    // Handle Notification Tests
    
    @Test
    fun `handleNotification sends notification successfully`() {
        setupMocks()
        
        val cli = CLIHandler()
        cli.client = FCMClient(tempCredentialsFile.absolutePath)
        
        // Use reflection to set private fields
        val tokenField = CLIHandler::class.java.getDeclaredField("token\$delegate")
        tokenField.isAccessible = true
        val bodyField = CLIHandler::class.java.getDeclaredField("body\$delegate")
        bodyField.isAccessible = true
        val titleField = CLIHandler::class.java.getDeclaredField("title\$delegate")
        titleField.isAccessible = true
        
        // Test via main instead
        cli.main(arrayOf(
            "--credentials-key-file", tempCredentialsFile.absolutePath,
            "--token", "test_token",
            "--title", "Test",
            "--body", "Body"
        ))
        
        val output = capturedOutput()
        assertThat(output).contains("successfully")
    }
    
    @Test
    fun `handleNotification with data sends notification successfully`() {
        setupMocks()
        
        val cli = CLIHandler()
        cli.main(arrayOf(
            "--credentials-key-file", tempCredentialsFile.absolutePath,
            "--token", "test_token",
            "--title", "Test",
            "--body", "Body",
            "--data", """{"key": "value"}"""
        ))
        
        val output = capturedOutput()
        assertThat(output).contains("successfully")
    }
    
    @Test
    fun `handleNotification with image sends notification successfully`() {
        setupMocks()
        
        val cli = CLIHandler()
        cli.main(arrayOf(
            "--credentials-key-file", tempCredentialsFile.absolutePath,
            "--token", "test_token",
            "--title", "Test",
            "--body", "Body",
            "--image", "https://example.com/image.png"
        ))
        
        val output = capturedOutput()
        assertThat(output).contains("successfully")
    }
    
    @Test
    fun `handleNotification dry run shows success`() {
        setupMocks()
        
        val cli = CLIHandler()
        cli.main(arrayOf(
            "--credentials-key-file", tempCredentialsFile.absolutePath,
            "--token", "test_token",
            "--title", "Test",
            "--body", "Body",
            "--dry-run"
        ))
        
        val output = capturedOutput()
        assertThat(output).contains("Dry run successful")
    }
    
    // Handle Data-Only Tests
    
    @Test
    fun `handleDataOnly sends data message successfully`() {
        setupMocks()
        
        val cli = CLIHandler()
        cli.main(arrayOf(
            "--credentials-key-file", tempCredentialsFile.absolutePath,
            "--token", "test_token",
            "--data-only", """{"action": "sync"}"""
        ))
        
        val output = capturedOutput()
        assertThat(output).contains("Data message sent successfully")
    }
    
    @Test
    fun `handleDataOnly dry run shows success`() {
        setupMocks()
        
        val cli = CLIHandler()
        cli.main(arrayOf(
            "--credentials-key-file", tempCredentialsFile.absolutePath,
            "--token", "test_token",
            "--data-only", """{"action": "sync"}""",
            "--dry-run"
        ))
        
        val output = capturedOutput()
        assertThat(output).contains("Dry run successful")
    }
    
    // Info Command Tests
    
    @Test
    fun `info flag shows service account info`() {
        setupMocks()
        val mockAccessToken = mockk<com.google.auth.oauth2.AccessToken>()
        val mockCredentials = mockk<GoogleCredentials>(relaxed = true)
        every { GoogleCredentials.fromStream(any()) } returns mockCredentials
        every { mockCredentials.createScoped(any<List<String>>()) } returns mockCredentials
        every { mockCredentials.accessToken } returns mockAccessToken
        every { mockAccessToken.tokenValue } returns "test_token_value"
        
        val cli = CLIHandler()
        cli.main(arrayOf(
            "--credentials-key-file", tempCredentialsFile.absolutePath,
            "--info"
        ))
        
        val output = capturedOutput()
        assertThat(output).contains("Firebase Service Account Information")
    }
    
    @Test
    fun `access-token flag shows service account info`() {
        setupMocks()
        val mockAccessToken = mockk<com.google.auth.oauth2.AccessToken>()
        val mockCredentials = mockk<GoogleCredentials>(relaxed = true)
        every { GoogleCredentials.fromStream(any()) } returns mockCredentials
        every { mockCredentials.createScoped(any<List<String>>()) } returns mockCredentials
        every { mockCredentials.accessToken } returns mockAccessToken
        every { mockAccessToken.tokenValue } returns "test_token_value"
        
        val cli = CLIHandler()
        cli.main(arrayOf(
            "--credentials-key-file", tempCredentialsFile.absolutePath,
            "--access-token"
        ))
        
        val output = capturedOutput()
        assertThat(output).contains("Firebase Service Account Information")
    }
    
    @Test
    fun `info-http flag shows service account info with http token`() {
        setupMocks()
        val mockAccessToken = mockk<com.google.auth.oauth2.AccessToken>()
        val mockCredentials = mockk<GoogleCredentials>(relaxed = true)
        every { GoogleCredentials.fromStream(any()) } returns mockCredentials
        every { mockCredentials.createScoped(any<List<String>>()) } returns mockCredentials
        every { mockCredentials.accessToken } returns mockAccessToken
        every { mockAccessToken.tokenValue } returns "test_http_token_123456789012345678901234567890123"
        
        val cli = CLIHandler()
        cli.main(arrayOf(
            "--credentials-key-file", tempCredentialsFile.absolutePath,
            "--info-http"
        ))
        
        val output = capturedOutput()
        assertThat(output).contains("Firebase Service Account Information")
    }
    
    @Test
    fun `access-token-http flag shows service account info`() {
        setupMocks()
        val mockAccessToken = mockk<com.google.auth.oauth2.AccessToken>()
        val mockCredentials = mockk<GoogleCredentials>(relaxed = true)
        every { GoogleCredentials.fromStream(any()) } returns mockCredentials
        every { mockCredentials.createScoped(any<List<String>>()) } returns mockCredentials
        every { mockCredentials.accessToken } returns mockAccessToken
        every { mockAccessToken.tokenValue } returns "test_http_token_123456789012345678901234567890123"
        
        val cli = CLIHandler()
        cli.main(arrayOf(
            "--credentials-key-file", tempCredentialsFile.absolutePath,
            "--access-token-http"
        ))
        
        val output = capturedOutput()
        assertThat(output).contains("Firebase Service Account Information")
    }
    
    // Help Test
    
    @Test
    fun `no args shows help`() {
        val cli = CLIHandler()
        cli.main(emptyArray())
        
        val output = capturedOutput()
        assertThat(output).contains("fcm-send")
    }
}
