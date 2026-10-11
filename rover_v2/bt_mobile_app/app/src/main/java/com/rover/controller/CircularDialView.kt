package com.rover.controller

import android.content.Context
import android.graphics.Canvas
import android.graphics.Paint
import android.graphics.Path
import android.util.AttributeSet
import android.view.MotionEvent
import android.view.View
import kotlin.math.atan2
import kotlin.math.cos
import kotlin.math.sin

class CircularDialView @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null,
    defStyleAttr: Int = 0
) : View(context, attrs, defStyleAttr) {

    private val circlePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        style = Paint.Style.STROKE
        strokeWidth = 8f
        color = 0xFF6200EE.toInt()
    }

    private val progressPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        style = Paint.Style.STROKE
        strokeWidth = 8f
        color = 0xFF018786.toInt()
    }

    private val indicatorPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        style = Paint.Style.FILL
        color = 0xFF018786.toInt()
    }

    private val textPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        textSize = 48f
        textAlign = Paint.Align.CENTER
        color = 0xFF212121.toInt()
    }

    private var centerX = 0f
    private var centerY = 0f
    private var radius = 0f

    private var isEnabled = true

    var maxAngle = 90
        set(value) {
            field = value
            invalidate()
        }

    var currentAngle = 0
        set(value) {
            field = value.coerceIn(0, maxAngle)
            invalidate()
        }

    private var onAngleChangedListener: ((Int) -> Unit)? = null

    fun setOnAngleChangedListener(listener: (Int) -> Unit) {
        onAngleChangedListener = listener
    }

    override fun setEnabled(enabled: Boolean) {
        super.setEnabled(enabled)
        isEnabled = enabled
        alpha = if (enabled) 1.0f else 0.5f
        invalidate()
    }

    override fun onSizeChanged(w: Int, h: Int, oldw: Int, oldh: Int) {
        super.onSizeChanged(w, h, oldw, oldh)
        centerX = w / 2f
        centerY = h / 2f
        radius = (minOf(w, h) / 2f) - 40f
    }

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)

        // Draw background circle
        canvas.drawCircle(centerX, centerY, radius, circlePaint)

        // Draw progress arc
        val sweepAngle = (currentAngle.toFloat() / maxAngle) * 360f
        val path = Path()
        path.addArc(
            centerX - radius,
            centerY - radius,
            centerX + radius,
            centerY + radius,
            -90f,
            sweepAngle
        )
        canvas.drawPath(path, progressPaint)

        // Draw indicator
        val angleInRadians = Math.toRadians((currentAngle.toDouble() / maxAngle * 360 - 90))
        val indicatorX = centerX + radius * cos(angleInRadians).toFloat()
        val indicatorY = centerY + radius * sin(angleInRadians).toFloat()
        canvas.drawCircle(indicatorX, indicatorY, 20f, indicatorPaint)

        // Draw angle text
        canvas.drawText("$currentAngle°", centerX, centerY + textPaint.textSize / 3, textPaint)
    }

    override fun onTouchEvent(event: MotionEvent): Boolean {
        if (!isEnabled) {
            return false
        }

        when (event.action) {
            MotionEvent.ACTION_DOWN, MotionEvent.ACTION_MOVE -> {
                val dx = event.x - centerX
                val dy = event.y - centerY
                val distance = kotlin.math.sqrt(dx * dx + dy * dy)

                if (distance <= radius + 50 && distance >= radius - 50) {
                    val angle = atan2(dy, dx)
                    val angleInDegrees = Math.toDegrees(angle.toDouble()).toFloat()
                    val normalizedAngle = ((angleInDegrees + 90) % 360 + 360) % 360
                    val newAngle = ((normalizedAngle / 360) * maxAngle).toInt().coerceIn(0, maxAngle)

                    if (currentAngle != newAngle) {
                        currentAngle = newAngle
                    }
                    return true
                }
            }
            MotionEvent.ACTION_UP -> {
                onAngleChangedListener?.invoke(currentAngle)
                return true
            }
        }
        return super.onTouchEvent(event)
    }
}
