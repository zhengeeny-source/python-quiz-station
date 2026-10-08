<script>
import { initializeAuth } from './stores/auth'

export default {
  onLaunch() {
    initializeAuth()
  },
}
</script>

<style>
page {
  min-height: 100%;
  background: #f5f7fb;
  color: #1d2939;
  font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", sans-serif;
  font-size: 28rpx;
}

view,
text,
button,
input,
textarea,
scroll-view,
picker {
  box-sizing: border-box;
}

button::after {
  border: 0;
}

.page-shell {
  padding: 28rpx 24rpx 48rpx;
}

.hero {
  margin-bottom: 24rpx;
}

.eyebrow {
  color: #2563eb;
  font-size: 22rpx;
  font-weight: 700;
  letter-spacing: 2rpx;
}

.page-title {
  display: block;
  margin-top: 8rpx;
  color: #101828;
  font-size: 44rpx;
  font-weight: 800;
  line-height: 1.25;
}

.page-subtitle {
  display: block;
  margin-top: 10rpx;
  color: #667085;
  font-size: 26rpx;
  line-height: 1.65;
}

.card {
  margin-bottom: 22rpx;
  padding: 28rpx;
  border: 2rpx solid #e4e7ec;
  border-radius: 24rpx;
  background: #ffffff;
  box-shadow: 0 10rpx 30rpx rgba(16, 24, 40, 0.05);
}

.primary-button,
.secondary-button,
.danger-button {
  min-height: 84rpx;
  border-radius: 18rpx;
  font-size: 29rpx;
  font-weight: 700;
  line-height: 84rpx;
}

.primary-button {
  background: #2563eb;
  color: #ffffff;
}

.primary-button[disabled] {
  background: #93b4f8;
  color: rgba(255, 255, 255, 0.9);
}

.secondary-button {
  border: 2rpx solid #d0d5dd;
  background: #ffffff;
  color: #344054;
}

.danger-button {
  border: 2rpx solid #fda29b;
  background: #fff5f4;
  color: #b42318;
}

.field-label {
  display: block;
  margin-bottom: 12rpx;
  color: #344054;
  font-size: 25rpx;
  font-weight: 700;
}

.text-input,
.text-area,
.picker-field {
  width: 100%;
  border: 2rpx solid #d0d5dd;
  border-radius: 16rpx;
  background: #ffffff;
  color: #101828;
  font-size: 28rpx;
}

.text-input,
.picker-field {
  min-height: 82rpx;
  padding: 0 22rpx;
  line-height: 82rpx;
}

.text-area {
  min-height: 190rpx;
  padding: 20rpx 22rpx;
  line-height: 1.6;
}

.form-field {
  margin-bottom: 24rpx;
}

.pill-row {
  display: flex;
  flex-wrap: wrap;
  gap: 14rpx;
}

.pill {
  padding: 14rpx 24rpx;
  border: 2rpx solid #d0d5dd;
  border-radius: 999rpx;
  background: #ffffff;
  color: #475467;
}

.pill.active {
  border-color: #2563eb;
  background: #eff6ff;
  color: #1d4ed8;
  font-weight: 700;
}

.success-text {
  color: #15803d;
}

.error-text {
  color: #b42318;
}

.empty-state {
  padding: 60rpx 20rpx;
  color: #667085;
  text-align: center;
}
</style>
