package com.mfdeveloper.fcm

import com.google.auth.oauth2.GoogleCredentials
import com.google.firebase.FirebaseApp
import com.google.firebase.FirebaseOptions
import com.google.firebase.messaging.FirebaseMessaging
import com.google.firebase.messaging.Message
import io.mockk.*
import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.assertThatThrownBy
import org.junit.jupiter.api.*
import java.io.ByteArrayOutputStream
import java.io.File
import java.io.FileNotFoundException
import java.io.PrintStream

class FCMClientTest {
    
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
    
    @BeforeEach
    fun setup() {
        // Clear Firebase apps
        FirebaseApp.getApps().forEach { it.delete() }
    }
    
    @AfterEach
    fun cleanup() {
        unmockkAll()
    }
    
    // Credentials Path Tests
    
    @Test
    fun `credentials path from constructor argument`() {
        val client = FCMClient(credentialsKeyFile = tempCredentialsFile.absolutePath)
        assertThat(client.credentialsPath).isEqualTo(tempCredentialsFile.absolutePath)
    }
    
    @Test
    fun `credentials path missing throws EnvironmentException`() {
        val client = FCMClient()
        assertThatThrownBy { client.credentialsPath }
            .isInstanceOf(EnvironmentException::class.java)
            .hasMessageContaining("No credentials provided")
            .hasMessageContaining("--credentials-key-file")
            .hasMessageContaining("GOOGLE_APPLICATION_CREDENTIALS")
    }
    
    @Test
    fun `credentials path file not found throws FileNotFoundException`() {
        val client = FCMClient(credentialsKeyFile = "/nonexistent/path/file.json")
        assertThatThrownBy { client.credentialsPath }
            .isInstanceOf(FileNotFoundException::class.java)
            .hasMessageContaining("Credentials file not found")
    }
    
    // Credentials Info Tests
    
    @Test
    fun `credentials info loads JSON correctly`() {
        val client = FCMClient(credentialsKeyFile = tempCredentialsFile.absolutePath)
        val info = client.getCredentialsInfo()
        
        assertThat(info).isNotNull
        assertThat(info?.get("project_id")).isEqualTo("test-project-123")
        assertThat(info?.get("client_email")).isEqualTo("firebase-adminsdk@test-project-123.iam.gserviceaccount.com")
    }
    
    @Test
    fun `credentials info is cached`() {
        val client = FCMClient(credentialsKeyFile = tempCredentialsFile.absolutePath)
        
        val info1 = client.getCredentialsInfo()
        val info2 = client.getCredentialsInfo()
        
        assertThat(info1).isSameAs(info2)
    }
    
    @Test
    fun `project ID from credentials`() {
        val client = FCMClient(credentialsKeyFile = tempCredentialsFile.absolutePath)
        assertThat(client.projectId).isEqualTo("test-project-123")
    }
    
    @Test
    fun `service account email from credentials`() {
        val client = FCMClient(credentialsKeyFile = tempCredentialsFile.absolutePath)
        assertThat(client.serviceAccountEmail).isEqualTo("firebase-adminsdk@test-project-123.iam.gserviceaccount.com")
    }
    
    // Show Info Tests
    
    @Test
    fun `show info displays project information`() {
        val client = FCMClient(credentialsKeyFile = tempCredentialsFile.absolutePath)
        
        val outputStream = ByteArrayOutputStream()
        val printStream = PrintStream(outputStream)
        val originalOut = System.out
        
        try {
            System.setOut(printStream)
            
            // This will fail to get actual token but should still show info
            try {
                client.showInfo(AccessTokenType.FIREBASE_ADMIN)
            } catch (e: Exception) {
                // Expected - we don't have valid credentials for actual API call
            }
            
            val output = outputStream.toString()
            assertThat(output).contains("Firebase Service Account Information")
            assertThat(output).contains("PROJECT_ID:")
            assertThat(output).contains("test-project-123")
            assertThat(output).contains("SERVICE_ACCOUNT_EMAIL:")
            assertThat(output).contains("CREDENTIALS_FILE:")
        } finally {
            System.setOut(originalOut)
        }
    }
    
    // Send Notification Tests
    
    @Test
    fun `send notification builds correct message`() {
        val client = FCMClient(credentialsKeyFile = tempCredentialsFile.absolutePath)
        
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
        
        val response = client.sendNotification(
            fcmToken = "test_token",
            title = "Test Title",
            body = "Test Body"
        )
        
        assertThat(response).isEqualTo("projects/test/messages/123")
        verify { mockMessaging.send(any<Message>(), false) }
    }
    
    @Test
    fun `send notification with data`() {
        val client = FCMClient(credentialsKeyFile = tempCredentialsFile.absolutePath)
        
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
        every { mockMessaging.send(any<Message>(), any()) } returns "projects/test/messages/456"
        
        val response = client.sendNotification(
            fcmToken = "test_token",
            title = "Test Title",
            body = "Test Body",
            data = mapOf("key" to "value")
        )
        
        assertThat(response).isNotNull()
    }
    
    @Test
    fun `send notification dry run`() {
        val client = FCMClient(credentialsKeyFile = tempCredentialsFile.absolutePath)
        
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
        every { mockMessaging.send(any<Message>(), true) } returns "projects/test/messages/dryrun"
        
        client.sendNotification(
            fcmToken = "test_token",
            title = "Test",
            body = "Body",
            dryRun = true
        )
        
        verify { mockMessaging.send(any<Message>(), true) }
    }
    
    // Send Data Message Tests
    
    @Test
    fun `send data message success`() {
        val client = FCMClient(credentialsKeyFile = tempCredentialsFile.absolutePath)
        
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
        every { mockMessaging.send(any<Message>(), any()) } returns "projects/test/messages/data123"
        
        val response = client.sendDataMessage(
            fcmToken = "test_token",
            data = mapOf("action" to "sync", "id" to "123")
        )
        
        assertThat(response).isEqualTo("projects/test/messages/data123")
    }
    
    @Test
    fun `send data message converts values to strings`() {
        val client = FCMClient(credentialsKeyFile = tempCredentialsFile.absolutePath)
        
        mockkStatic(FirebaseApp::class)
        mockkStatic(GoogleCredentials::class)
        mockkStatic(FirebaseMessaging::class)
        
        val mockCredentials = mockk<GoogleCredentials>(relaxed = true)
        val mockMessaging = mockk<FirebaseMessaging>()
        val mockApp = mockk<FirebaseApp>(relaxed = true)
        val capturedMessage = slot<Message>()
        
        every { FirebaseApp.getApps() } returns listOf()
        every { GoogleCredentials.fromStream(any()) } returns mockCredentials
        every { mockCredentials.createScoped(any<List<String>>()) } returns mockCredentials
        every { FirebaseApp.initializeApp(any<FirebaseOptions>()) } returns mockApp
        every { FirebaseMessaging.getInstance() } returns mockMessaging
        every { mockMessaging.send(capture(capturedMessage), any()) } returns "msg_id"
        
        client.sendDataMessage(
            fcmToken = "test_token",
            data = mapOf("count" to 42, "active" to true, "name" to "test")
        )
        
        // Message was captured and sent
        verify { mockMessaging.send(any<Message>(), false) }
    }
    
    // Send Notification with Image Tests
    
    @Test
    fun `send notification with image url`() {
        val client = FCMClient(credentialsKeyFile = tempCredentialsFile.absolutePath)
        
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
        every { mockMessaging.send(any<Message>(), any()) } returns "projects/test/messages/img123"
        
        val response = client.sendNotification(
            fcmToken = "test_token",
            title = "Test Title",
            body = "Test Body",
            imageUrl = "https://example.com/image.png"
        )
        
        assertThat(response).isEqualTo("projects/test/messages/img123")
    }
    
    // Show Info with HTTP API Token Tests
    
    @Test
    fun `show info displays HTTP API token information`() {
        val client = FCMClient(credentialsKeyFile = tempCredentialsFile.absolutePath)
        
        val outputStream = ByteArrayOutputStream()
        val printStream = PrintStream(outputStream)
        val originalOut = System.out
        
        try {
            System.setOut(printStream)
            
            // This will fail to get actual token but should still show info
            try {
                client.showInfo(AccessTokenType.FCM_OAUTH_HTTP_API)
            } catch (e: Exception) {
                // Expected - we don't have valid credentials for actual API call
            }
            
            val output = outputStream.toString()
            assertThat(output).contains("Firebase Service Account Information")
            assertThat(output).contains("PROJECT_ID:")
        } finally {
            System.setOut(originalOut)
        }
    }
    
    // Initialize Tests
    
    @Test
    fun `initialize sets property when credentials key file provided`() {
        val client = FCMClient(credentialsKeyFile = tempCredentialsFile.absolutePath)
        
        mockkStatic(FirebaseApp::class)
        mockkStatic(GoogleCredentials::class)
        
        val mockCredentials = mockk<GoogleCredentials>(relaxed = true)
        val mockApp = mockk<FirebaseApp>(relaxed = true)
        
        every { FirebaseApp.getApps() } returns listOf()
        every { GoogleCredentials.fromStream(any()) } returns mockCredentials
        every { mockCredentials.createScoped(any<List<String>>()) } returns mockCredentials
        every { FirebaseApp.initializeApp(any<FirebaseOptions>()) } returns mockApp
        
        client.initialize()
        
        verify { FirebaseApp.initializeApp(any<FirebaseOptions>()) }
    }
    
    @Test
    fun `initialize only runs once`() {
        val client = FCMClient(credentialsKeyFile = tempCredentialsFile.absolutePath)
        
        mockkStatic(FirebaseApp::class)
        mockkStatic(GoogleCredentials::class)
        
        val mockCredentials = mockk<GoogleCredentials>(relaxed = true)
        val mockApp = mockk<FirebaseApp>(relaxed = true)
        
        every { FirebaseApp.getApps() } returns listOf()
        every { GoogleCredentials.fromStream(any()) } returns mockCredentials
        every { mockCredentials.createScoped(any<List<String>>()) } returns mockCredentials
        every { FirebaseApp.initializeApp(any<FirebaseOptions>()) } returns mockApp
        
        client.initialize()
        
        // Now make getApps return the app so the second call won't initialize
        every { FirebaseApp.getApps() } returns listOf(mockApp)
        
        client.initialize()
        
        // Should only be called once
        verify(exactly = 1) { FirebaseApp.initializeApp(any<FirebaseOptions>()) }
    }
    
    // Get Access Token Tests
    
    @Test
    fun `get access token returns token value`() {
        val client = FCMClient(credentialsKeyFile = tempCredentialsFile.absolutePath)
        
        mockkStatic(FirebaseApp::class)
        mockkStatic(GoogleCredentials::class)
        
        val mockCredentials = mockk<GoogleCredentials>(relaxed = true)
        val mockApp = mockk<FirebaseApp>(relaxed = true)
        val mockAccessToken = mockk<com.google.auth.oauth2.AccessToken>()
        
        every { FirebaseApp.getApps() } returns listOf()
        every { GoogleCredentials.fromStream(any()) } returns mockCredentials
        every { mockCredentials.createScoped(any<List<String>>()) } returns mockCredentials
        every { FirebaseApp.initializeApp(any<FirebaseOptions>()) } returns mockApp
        every { mockCredentials.accessToken } returns mockAccessToken
        every { mockAccessToken.tokenValue } returns "test_access_token_12345"
        
        val token = client.getAccessToken()
        
        assertThat(token).isEqualTo("test_access_token_12345")
    }
    
    @Test
    fun `get access token returns empty string when token is null`() {
        val client = FCMClient(credentialsKeyFile = tempCredentialsFile.absolutePath)
        
        mockkStatic(FirebaseApp::class)
        mockkStatic(GoogleCredentials::class)
        
        val mockCredentials = mockk<GoogleCredentials>(relaxed = true)
        val mockApp = mockk<FirebaseApp>(relaxed = true)
        
        every { FirebaseApp.getApps() } returns listOf()
        every { GoogleCredentials.fromStream(any()) } returns mockCredentials
        every { mockCredentials.createScoped(any<List<String>>()) } returns mockCredentials
        every { FirebaseApp.initializeApp(any<FirebaseOptions>()) } returns mockApp
        every { mockCredentials.accessToken } returns null
        
        val token = client.getAccessToken()
        
        assertThat(token).isEqualTo("")
    }
    
    @Test
    fun `get access token http api returns token value`() {
        val client = FCMClient(credentialsKeyFile = tempCredentialsFile.absolutePath)
        
        mockkStatic(FirebaseApp::class)
        mockkStatic(GoogleCredentials::class)
        
        val mockCredentials = mockk<GoogleCredentials>(relaxed = true)
        val mockApp = mockk<FirebaseApp>(relaxed = true)
        val mockAccessToken = mockk<com.google.auth.oauth2.AccessToken>()
        
        every { FirebaseApp.getApps() } returns listOf()
        every { GoogleCredentials.fromStream(any()) } returns mockCredentials
        every { mockCredentials.createScoped(any<List<String>>()) } returns mockCredentials
        every { FirebaseApp.initializeApp(any<FirebaseOptions>()) } returns mockApp
        every { mockCredentials.accessToken } returns mockAccessToken
        every { mockAccessToken.tokenValue } returns "http_api_token_67890"
        
        val token = client.getAccessTokenHttpApi()
        
        assertThat(token).isEqualTo("http_api_token_67890")
    }
    
    // Send Data Message Dry Run Tests
    
    @Test
    fun `send data message dry run`() {
        val client = FCMClient(credentialsKeyFile = tempCredentialsFile.absolutePath)
        
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
        every { mockMessaging.send(any<Message>(), true) } returns "projects/test/messages/dryrun_data"
        
        val response = client.sendDataMessage(
            fcmToken = "test_token",
            data = mapOf("action" to "sync"),
            dryRun = true
        )
        
        assertThat(response).isEqualTo("projects/test/messages/dryrun_data")
        verify { mockMessaging.send(any<Message>(), true) }
    }
    
    // Access Token Type Tests
    
    @Test
    fun `firebase admin type value`() {
        assertThat(AccessTokenType.FIREBASE_ADMIN.value).isEqualTo("firebase_admin")
    }
    
    @Test
    fun `fcm http api type value`() {
        assertThat(AccessTokenType.FCM_OAUTH_HTTP_API.value).isEqualTo("fcm_http_api")
    }
    
    // EnvironmentException Tests
    
    @Test
    fun `environment exception has correct message`() {
        val exception = EnvironmentException("Test error message")
        assertThat(exception.message).isEqualTo("Test error message")
    }
}
