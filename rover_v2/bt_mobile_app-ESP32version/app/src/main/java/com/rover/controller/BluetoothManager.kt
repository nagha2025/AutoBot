package com.rover.controller

import android.annotation.SuppressLint
import android.bluetooth.BluetoothAdapter
import android.bluetooth.BluetoothDevice
import android.bluetooth.BluetoothSocket
import android.content.Context
import android.content.pm.PackageManager
import android.os.Build
import android.util.Log
import androidx.core.app.ActivityCompat
import java.io.IOException
import java.io.OutputStream
import java.util.UUID

class BluetoothManager(private val context: Context) {
    
    private val bluetoothAdapter: BluetoothAdapter? = BluetoothAdapter.getDefaultAdapter()
    private var bluetoothSocket: BluetoothSocket? = null
    private var outputStream: OutputStream? = null
    
    // Standard SPP UUID
    private val uuid: UUID = UUID.fromString("00001101-0000-1000-8000-00805F9B34FB")
    
    companion object {
        private const val TAG = "BluetoothManager"
    }
    
    fun isBluetoothSupported(): Boolean {
        return bluetoothAdapter != null
    }
    
    fun isBluetoothEnabled(): Boolean {
        return bluetoothAdapter?.isEnabled == true
    }
    
    fun enableBluetooth(): Boolean {
        return bluetoothAdapter?.enable() == true
    }
    
    @SuppressLint("MissingPermission")
    fun getPairedDevices(): Set<BluetoothDevice> {
        if (!hasBluetoothPermissions()) {
            return emptySet()
        }
        return bluetoothAdapter?.bondedDevices ?: emptySet()
    }
    
    @SuppressLint("MissingPermission")
    fun connectToDevice(device: BluetoothDevice): Boolean {
        try {
            if (bluetoothSocket?.isConnected == true) {
                disconnect()
            }

            // Try primary connection method
            try {
                bluetoothSocket = device.createRfcommSocketToServiceRecord(uuid)
                bluetoothSocket?.connect()
                outputStream = bluetoothSocket?.outputStream

                Log.d(TAG, "Connected to ${device.name}")
                return true
            } catch (e1: IOException) {
                Log.w(TAG, "Primary connection method failed: ${e1.message}, trying fallback...")

                // Fallback: try to connect on different channels
                for (channel in 1..10) {
                    try {
                        val fallbackSocket = device.javaClass.getMethod(
                            "createRfcommSocket",
                            Int::class.javaPrimitiveType
                        ).invoke(device, channel) as BluetoothSocket

                        fallbackSocket.connect()
                        bluetoothSocket = fallbackSocket
                        outputStream = bluetoothSocket?.outputStream

                        Log.d(TAG, "Connected to ${device.name} on channel $channel")
                        return true
                    } catch (e2: Exception) {
                        Log.d(TAG, "Channel $channel failed: ${e2.message}")
                        continue
                    }
                }

                Log.e(TAG, "All connection methods failed")
                disconnect()
                return false
            }
        } catch (e: Exception) {
            Log.e(TAG, "Connection failed: ${e.message}")
            disconnect()
            return false
        }
    }
    
    fun sendCommand(command: String): Boolean {
        if (outputStream == null) {
            Log.e(TAG, "Not connected to any device")
            return false
        }
        
        return try {
            outputStream?.write(command.toByteArray())
            outputStream?.flush()
            Log.d(TAG, "Command sent: $command")
            true
        } catch (e: IOException) {
            Log.e(TAG, "Failed to send command: ${e.message}")
            false
        }
    }
    
    fun disconnect() {
        try {
            outputStream?.close()
            bluetoothSocket?.close()
        } catch (e: IOException) {
            Log.e(TAG, "Error closing connection: ${e.message}")
        } finally {
            outputStream = null
            bluetoothSocket = null
        }
    }
    
    fun isConnected(): Boolean {
        return bluetoothSocket?.isConnected == true
    }
    
    private fun hasBluetoothPermissions(): Boolean {
        val permissions = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            arrayOf(
                android.Manifest.permission.BLUETOOTH_CONNECT,
                android.Manifest.permission.BLUETOOTH_SCAN
            )
        } else {
            arrayOf(
                android.Manifest.permission.BLUETOOTH,
                android.Manifest.permission.BLUETOOTH_ADMIN
            )
        }
        
        return permissions.all {
            ActivityCompat.checkSelfPermission(context, it) == PackageManager.PERMISSION_GRANTED
        }
    }
}
