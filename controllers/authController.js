import crypto from 'crypto';
import bcrypt from 'bcryptjs';
import User from '../models/User.js';
import sendEmail from '../utils/sendEmail.js';

const RESET_TOKEN_TTL_MS = 10 * 60 * 1000; // 10 minutes
const MIN_PASSWORD_LENGTH = 8;

// @desc    Forgot Password
// @route   POST /auth/forgot-password
// @access  Public
export const forgotPassword = async (req, res) => {
  try {
    const email = (req.body?.email || '').toString().trim().toLowerCase();
    if (!email) {
      return res.status(400).json({ message: 'Email is required' });
    }

    const user = await User.findOne({ email });

    // SECURITY: Do not reveal whether the email is registered.
    // Always return 200 with a generic message, whether or not the
    // user exists. Otherwise an attacker can enumerate valid emails.
    if (!user) {
      return res.status(200).json({
        success: true,
        message: 'If that email exists, a reset link has been sent.',
      });
    }

    // Generate a random reset token
    const resetToken = crypto.randomBytes(32).toString('hex');

    // Hash token and set to resetPasswordToken field
    user.resetPasswordToken = crypto
      .createHash('sha256')
      .update(resetToken)
      .digest('hex');

    // Store expiry as Date (Mongoose-friendly, no cast ambiguity)
    user.resetPasswordExpire = new Date(Date.now() + RESET_TOKEN_TTL_MS);

    // Bypass validation: we only changed reset fields
    await user.save({ validateBeforeSave: false });

    // Create reset URL
    const resetUrl = `${process.env.FRONTEND_URL}/reset-password/${resetToken}`;

    const message =
      `You are receiving this email because you (or someone else) has ` +
      `requested the reset of a password. Please click the link to reset: \n\n ` +
      `${resetUrl}`;

    try {
      await sendEmail({
        email: user.email,
        subject: 'Password Reset Request',
        message,
      });
      return res.status(200).json({
        success: true,
        message: 'If that email exists, a reset link has been sent.',
      });
    } catch (err) {
      // Roll back the token so it can't be reused if email failed
      user.resetPasswordToken = undefined;
      user.resetPasswordExpire = undefined;
      await user.save({ validateBeforeSave: false });

      // Do NOT log the email
      console.error('[forgotPassword] email send failed:', err.message);
      return res.status(500).json({ message: 'Email could not be sent' });
    }
  } catch (error) {
    console.error('[forgotPassword] error:', error.message);
    res.status(500).json({ message: 'Server Error' });
  }
};

// @desc    Reset Password
// @route   POST /auth/reset-password
// @access  Public
export const resetPassword = async (req, res) => {
  try {
    const token = (req.body?.token || '').toString().trim();
    const new_password = (req.body?.new_password || '').toString();

    if (!token) {
      return res.status(400).json({ message: 'Reset token is required' });
    }
    if (new_password.length < MIN_PASSWORD_LENGTH) {
      return res.status(400).json({
        message: `Password must be at least ${MIN_PASSWORD_LENGTH} characters`,
      });
    }

    // Get hashed token
    const resetPasswordToken = crypto
      .createHash('sha256')
      .update(token)
      .digest('hex');

    // Find user with non-expired token
    const user = await User.findOne({
      resetPasswordToken,
      resetPasswordExpire: { $gt: new Date() },
    });

    if (!user) {
      return res.status(400).json({ message: 'Invalid or expired token' });
    }

    // CRITICAL: do NOT manually hash here.
    // If the User model has a pre('save') hook that hashes `password`
    // (the standard Mongoose pattern), hashing here would double-hash
    // the value, and the stored hash would never match at login.
    // Just assign the plain password and let the hook hash it.
    user.password = new_password;

    // Clear token fields
    user.resetPasswordToken = undefined;
    user.resetPasswordExpire = undefined;

    // validateBeforeSave: true (default) so password rules still apply
    await user.save();

    return res.status(200).json({ success: true, message: 'Password reset successful' });
  } catch (error) {
    console.error('[resetPassword] error:', error.message);
    res.status(500).json({ message: 'Server Error' });
  }
};