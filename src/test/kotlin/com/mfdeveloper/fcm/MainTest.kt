package com.mfdeveloper.fcm

import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.AfterEach
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.DisplayName
import org.junit.jupiter.api.Test
import java.io.ByteArrayOutputStream
import java.io.PrintStream

@DisplayName("Main Entry Point Tests")
class MainTest {
    
    private lateinit var originalOut: PrintStream
    private lateinit var outputStream: ByteArrayOutputStream
    
    @BeforeEach
    fun setup() {
        originalOut = System.out
        outputStream = ByteArrayOutputStream()
        System.setOut(PrintStream(outputStream))
    }
    
    @AfterEach
    fun restore() {
        System.setOut(originalOut)
    }
    
    @Test
    fun `main function shows help when no args`() {
        main(emptyArray())
        
        val output = outputStream.toString()
        assertThat(output).contains("fcm-send")
    }
}
