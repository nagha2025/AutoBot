package com.rover.controller

import android.Manifest
import android.annotation.SuppressLint
import android.bluetooth.BluetoothDevice
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.view.MotionEvent
import android.view.View
import android.widget.AdapterView
import android.widget.ArrayAdapter
import android.widget.Button
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat

class MainActivity : AppCompatActivity() {
    
    private lateinit var bluetoothManager: BluetoothManager
    private lateinit var statusText: TextView
    private lateinit var deviceSpinner: androidx.appcompat.widget.AppCompatSpinner
    private lateinit var connectButton: Button
    private lateinit var disconnectButton: Button
    
    // Direction buttons
    private lateinit var btnForward: Button
    private lateinit var btnBackward: Button
    private lateinit var btnLeft: Button
    private lateinit var btnRight: Button
    private lateinit var btnStop: Button
    
    // Speed control
    private lateinit var btnIncreaseSpeed: Button
    private lateinit var btnDecreaseSpeed: Button
    private lateinit var speedText: TextView
    private var currentSpeed = 0.5
    
    // Lateral movement
    private lateinit var btnLateralLeft: Button
    private lateinit var btnLateralRight: Button
    
    private val PERMISSION_REQUEST_CODE = 100
    private val PERMISSIONS = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
        arrayOf(
            Manifest.permission.BLUETOOTH_SCAN,
            Manifest.permission.BLUETOOTH_CONNECT,
            Manifest.permission.ACCESS_FINE_LOCATION
        )
    } else {
        arrayOf(
            Manifest.permission.BLUETOOTH,
            Manifest.permission.BLUETOOTH_ADMIN,
            Manifest.permission.ACCESS_FINE_LOCATION
        )
    }
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        
        bluetoothManager = BluetoothManager(this)
        
        initViews()
        checkPermissions()
        loadPairedDevices()
        updateSpeedDisplay()
    }
    
    private fun initViews() {
        statusText = findViewById(R.id.statusText)
        deviceSpinner = findViewById(R.id.deviceSpinner)
        connectButton = findViewById(R.id.connectButton)
        disconnectButton = findViewById(R.id.disconnectButton)
        
        btnForward = findViewById(R.id.btnForward)
        btnBackward = findViewById(R.id.btnBackward)
        btnLeft = findViewById(R.id.btnLeft)
        btnRight = findViewById(R.id.btnRight)
        btnStop = findViewById(R.id.btnStop)
        
        btnIncreaseSpeed = findViewById(R.id.btnIncreaseSpeed)
        btnDecreaseSpeed = findViewById(R.id.btnDecreaseSpeed)
        speedText = findViewById(R.id.speedText)
        
        btnLateralLeft = findViewById(R.id.btnLateralLeft)
        btnLateralRight = findViewById(R.id.btnLateralRight)
        
        connectButton.setOnClickListener {
            connectToDevice()
        }
        
        disconnectButton.setOnClickListener {
            disconnectDevice()
        }
        
        setupDirectionButtons()
        setupSpeedButtons()
        setupLateralButtons()
        disableDirectionButtons()
    }
    
    private fun setupDirectionButtons() {
        btnForward.setOnTouchListener { _, event ->
            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    sendMoveCommand(currentSpeed)
                    true
                }
                MotionEvent.ACTION_UP -> {
                    sendStopCommand()
                    true
                }
                else -> false
            }
        }
        
        btnBackward.setOnTouchListener { _, event ->
            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    sendMoveCommand(-currentSpeed)
                    true
                }
                MotionEvent.ACTION_UP -> {
                    sendStopCommand()
                    true
                }
                else -> false
            }
        }
        
        btnLeft.setOnTouchListener { _, event ->
            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    sendMecanumCommand(0.0, 0.0, -currentSpeed)
                    true
                }
                MotionEvent.ACTION_UP -> {
                    sendStopCommand()
                    true
                }
                else -> false
            }
        }

        btnRight.setOnTouchListener { _, event ->
            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    sendMecanumCommand(0.0, 0.0, currentSpeed)
                    true
                }
                MotionEvent.ACTION_UP -> {
                    sendStopCommand()
                    true
                }
                else -> false
            }
        }
        
        btnStop.setOnClickListener {
            sendStopCommand()
        }
    }
    
    private fun setupSpeedButtons() {
        btnIncreaseSpeed.setOnClickListener {
            if (currentSpeed < 1.0) {
                currentSpeed = (currentSpeed + 0.1).coerceAtMost(1.0)
                updateSpeedDisplay()
            }
        }
        
        btnDecreaseSpeed.setOnClickListener {
            if (currentSpeed > 0.5) {
                currentSpeed = (currentSpeed - 0.1).coerceAtLeast(0.5)
                updateSpeedDisplay()
            }
        }
    }
    
    private fun updateSpeedDisplay() {
        speedText.text = "Speed: ${String.format("%.1f", currentSpeed)}"
    }

    private fun setupLateralButtons() {
        btnLateralLeft.setOnTouchListener { _, event ->
            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    sendMecanumCommand(0.0, -currentSpeed, 0.0)
                    true
                }
                MotionEvent.ACTION_UP -> {
                    sendStopCommand()
                    true
                }
                else -> false
            }
        }
        
        btnLateralRight.setOnTouchListener { _, event ->
            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    sendMecanumCommand(0.0, currentSpeed, 0.0)
                    true
                }
                MotionEvent.ACTION_UP -> {
                    sendStopCommand()
                    true
                }
                else -> false
            }
        }
    }

    private fun checkPermissions() {
        val missingPermissions = PERMISSIONS.filter {
            ContextCompat.checkSelfPermission(this, it) != PackageManager.PERMISSION_GRANTED
        }
        
        if (missingPermissions.isNotEmpty()) {
            ActivityCompat.requestPermissions(this, missingPermissions.toTypedArray(), PERMISSION_REQUEST_CODE)
        }
    }
    
    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == PERMISSION_REQUEST_CODE) {
            if (grantResults.isNotEmpty() && grantResults.all { it == PackageManager.PERMISSION_GRANTED }) {
                loadPairedDevices()
            } else {
                Toast.makeText(this, "Bluetooth permissions required", Toast.LENGTH_LONG).show()
            }
        }
    }
    
    @SuppressLint("MissingPermission")
    private fun loadPairedDevices() {
        if (!bluetoothManager.isBluetoothSupported()) {
            statusText.text = "Bluetooth not supported on this device"
            return
        }
        
        if (!bluetoothManager.isBluetoothEnabled()) {
            statusText.text = "Bluetooth is disabled. Please enable it."
            return
        }
        
        val devices = bluetoothManager.getPairedDevices()
        if (devices.isEmpty()) {
            statusText.text = "No paired devices found. Pair your Raspberry Pi first."
            return
        }
        
        val deviceNames = devices.map { "${it.name} (${it.address})" }
        val adapter = ArrayAdapter(this, android.R.layout.simple_spinner_item, deviceNames)
        adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item)
        deviceSpinner.adapter = adapter
        
        statusText.text = "Found ${devices.size} paired device(s)"
    }
    
    @SuppressLint("MissingPermission")
    private fun connectToDevice() {
        val selectedPosition = deviceSpinner.selectedItemPosition
        if (selectedPosition == AdapterView.INVALID_POSITION) {
            Toast.makeText(this, "Please select a device", Toast.LENGTH_SHORT).show()
            return
        }
        
        val devices = bluetoothManager.getPairedDevices().toList()
        if (selectedPosition >= devices.size) {
            Toast.makeText(this, "Invalid device selection", Toast.LENGTH_SHORT).show()
            return
        }
        
        val device = devices[selectedPosition]
        
        statusText.text = "Connecting to ${device.name}..."
        
        Thread {
            val connected = bluetoothManager.connectToDevice(device)
            Handler(Looper.getMainLooper()).post {
                if (connected) {
                    statusText.text = "Connected to ${device.name}"
                    enableDirectionButtons()
                    connectButton.isEnabled = false
                    disconnectButton.isEnabled = true
                    deviceSpinner.isEnabled = false
                } else {
                    statusText.text = "Failed to connect to ${device.name}"
                }
            }
        }.start()
    }
    
    private fun disconnectDevice() {
        bluetoothManager.disconnect()
        statusText.text = "Disconnected"
        disableDirectionButtons()
        connectButton.isEnabled = true
        disconnectButton.isEnabled = false
        deviceSpinner.isEnabled = true
    }
    
    private fun sendMoveCommand(speed: Double) {
        sendMoveCommand(speed, speed, speed, speed)
    }
    
    private fun sendMoveCommand(fl: Double, fr: Double, bl: Double, br: Double) {
        // Apply scaling to balance front and rear motors
        // Reduce rear wheel speed by 20% to match front wheel power
        val rearScaling = 0.8
        val adjustedBl = bl * rearScaling
        val adjustedBr = br * rearScaling

        val command = "MOVE ${String.format("%.1f", fl)} ${String.format("%.1f", fr)} ${String.format("%.1f", adjustedBl)} ${String.format("%.1f", adjustedBr)}"
        sendCommand(command)
    }

    private fun sendMecanumCommand(x: Double, y: Double, rotation: Double) {
        val command = "MECANUM ${String.format("%.1f", x)} ${String.format("%.1f", y)} ${String.format("%.1f", rotation)}"
        sendCommand(command)
    }

    private fun sendStopCommand() {
        sendCommand("STOP")
    }
    
    private fun sendCommand(command: String) {
        if (!bluetoothManager.isConnected()) {
            Toast.makeText(this, "Not connected to device", Toast.LENGTH_SHORT).show()
            return
        }
        
        Thread {
            val success = bluetoothManager.sendCommand(command)
            Handler(Looper.getMainLooper()).post {
                if (!success) {
                    Toast.makeText(this, "Failed to send command", Toast.LENGTH_SHORT).show()
                }
            }
        }.start()
    }
    
    private fun enableDirectionButtons() {
        btnForward.isEnabled = true
        btnBackward.isEnabled = true
        btnLeft.isEnabled = true
        btnRight.isEnabled = true
        btnStop.isEnabled = true
        btnIncreaseSpeed.isEnabled = true
        btnDecreaseSpeed.isEnabled = true
        btnLateralLeft.isEnabled = true
        btnLateralRight.isEnabled = true
    }

    private fun disableDirectionButtons() {
        btnForward.isEnabled = false
        btnBackward.isEnabled = false
        btnLeft.isEnabled = false
        btnRight.isEnabled = false
        btnStop.isEnabled = false
        btnIncreaseSpeed.isEnabled = false
        btnDecreaseSpeed.isEnabled = false
        btnLateralLeft.isEnabled = false
        btnLateralRight.isEnabled = false
    }
    
    override fun onDestroy() {
        super.onDestroy()
        bluetoothManager.disconnect()
    }
}
