"""Constants for the Garmin Connect integration."""
from homeassistant.const import DEVICE_CLASS_TIMESTAMP

DOMAIN = "garmin_connect"
ATTRIBUTION = "Data provided by garmin.com"

GARMIN_ENTITY_LIST = {
    "totalSteps": ["Total Steps", "steps", "mdi:walk", None, True],
    "dailyStepGoal": ["Daily Step Goal", "steps", "mdi:walk", None, True],
    "totalKilocalories": ["Total KiloCalories", "kcal", "mdi:food", None, True],
    "activeKilocalories": ["Active KiloCalories", "kcal", "mdi:food", None, True],
    "bmrKilocalories": ["BMR KiloCalories", "kcal", "mdi:food", None, True],
    "consumedKilocalories": ["Consumed KiloCalories", "kcal", "mdi:food", None, False],
    "burnedKilocalories": ["Burned KiloCalories", "kcal", "mdi:food", None, True],
    "remainingKilocalories": [
        "Remaining KiloCalories",
        "kcal",
        "mdi:food",
        None,
        False,
    ],
    "netRemainingKilocalories": [
        "Net Remaining KiloCalories",
        "kcal",
        "mdi:food",
        None,
        False,
    ],
    "netCalorieGoal": ["Net Calorie Goal", "cal", "mdi:food", None, False],
    "totalDistanceMeters": ["Total Distance Mtr", "m", "mdi:walk", None, True],
    "wellnessStartTimeLocal": [
        "Wellness Start Time",
        "",
        "mdi:clock",
        DEVICE_CLASS_TIMESTAMP,
        False,
    ],
    "wellnessEndTimeLocal": [
        "Wellness End Time",
        "",
        "mdi:clock",
        DEVICE_CLASS_TIMESTAMP,
        False,
    ],
    "wellnessDescription": ["Wellness Description", "", "mdi:clock", None, False],
    "wellnessDistanceMeters": ["Wellness Distance Mtr", "m", "mdi:walk", None, False],
    "wellnessActiveKilocalories": [
        "Wellness Active KiloCalories",
        "kcal",
        "mdi:food",
        None,
        False,
    ],
    "wellnessKilocalories": ["Wellness KiloCalories", "kcal", "mdi:food", None, False],
    "highlyActiveSeconds": ["Highly Active Time", "min", "mdi:fire", None, False],
    "activeSeconds": ["Active Time", "min", "mdi:fire", None, True],
    "sedentarySeconds": ["Sedentary Time", "min", "mdi:seat", None, True],
    "sleepingSeconds": ["Sleeping Time", "min", "mdi:sleep", None, True],
    "measurableAwakeDuration": ["Awake Duration", "min", "mdi:sleep", None, True],
    "measurableAsleepDuration": ["Sleep Duration", "min", "mdi:sleep", None, True],
    "floorsAscendedInMeters": ["Floors Ascended Mtr", "m", "mdi:stairs", None, False],
    "floorsDescendedInMeters": [
        "Floors Descended Mtr",
        "m",
        "mdi:stairs",
        None,
        False,
    ],
    "floorsAscended": ["Floors Ascended", "floors", "mdi:stairs", None, True],
    "floorsDescended": ["Floors Descended", "floors", "mdi:stairs", None, True],
    "userFloorsAscendedGoal": [
        "Floors Ascended Goal",
        "floors",
        "mdi:stairs",
        None,
        True,
    ],
    "minHeartRate": ["Min Heart Rate", "bpm", "mdi:heart-pulse", None, True],
    "maxHeartRate": ["Max Heart Rate", "bpm", "mdi:heart-pulse", None, True],
    "restingHeartRate": ["Resting Heart Rate", "bpm", "mdi:heart-pulse", None, True],
    "minAvgHeartRate": ["Min Avg Heart Rate", "bpm", "mdi:heart-pulse", None, False],
    "maxAvgHeartRate": ["Max Avg Heart Rate", "bpm", "mdi:heart-pulse", None, False],
    "abnormalHeartRateAlertsCount": [
        "Abnormal HR Counts",
        "",
        "mdi:heart-pulse",
        None,
        False,
    ],
    "lastSevenDaysAvgRestingHeartRate": [
        "Last 7 Days Avg Heart Rate",
        "bpm",
        "mdi:heart-pulse",
        None,
        False,
    ],
    "averageStressLevel": ["Avg Stress Level", "", "mdi:flash-alert", None, True],
    "maxStressLevel": ["Max Stress Level", "", "mdi:flash-alert", None, True],
    "stressQualifier": ["Stress Qualifier", "", "mdi:flash-alert", None, False],
    "stressDuration": ["Stress Duration", "min", "mdi:flash-alert", None, False],
    "restStressDuration": [
        "Rest Stress Duration",
        "min",
        "mdi:flash-alert",
        None,
        True,
    ],
    "activityStressDuration": [
        "Activity Stress Duration",
        "min",
        "mdi:flash-alert",
        None,
        True,
    ],
    "uncategorizedStressDuration": [
        "Uncat. Stress Duration",
        "min",
        "mdi:flash-alert",
        None,
        True,
    ],
    "totalStressDuration": [
        "Total Stress Duration",
        "min",
        "mdi:flash-alert",
        None,
        True,
    ],
    "lowStressDuration": ["Low Stress Duration", "min", "mdi:flash-alert", None, True],
    "mediumStressDuration": [
        "Medium Stress Duration",
        "min",
        "mdi:flash-alert",
        None,
        True,
    ],
    "highStressDuration": [
        "High Stress Duration",
        "min",
        "mdi:flash-alert",
        None,
        True,
    ],
    "stressPercentage": ["Stress Percentage", "%", "mdi:flash-alert", None, False],
    "restStressPercentage": [
        "Rest Stress Percentage",
        "%",
        "mdi:flash-alert",
        None,
        False,
    ],
    "activityStressPercentage": [
        "Activity Stress Percentage",
        "%",
        "mdi:flash-alert",
        None,
        False,
    ],
    "uncategorizedStressPercentage": [
        "Uncat. Stress Percentage",
        "%",
        "mdi:flash-alert",
        None,
        False,
    ],
    "lowStressPercentage": [
        "Low Stress Percentage",
        "%",
        "mdi:flash-alert",
        None,
        False,
    ],
    "mediumStressPercentage": [
        "Medium Stress Percentage",
        "%",
        "mdi:flash-alert",
        None,
        False,
    ],
    "highStressPercentage": [
        "High Stress Percentage",
        "%",
        "mdi:flash-alert",
        None,
        False,
    ],
    "moderateIntensityMinutes": [
        "Moderate Intensity",
        "min",
        "mdi:flash-alert",
        None,
        False,
    ],
    "vigorousIntensityMinutes": [
        "Vigorous Intensity",
        "min",
        "mdi:run-fast",
        None,
        False,
    ],
    "intensityMinutesGoal": ["Intensity Goal", "min", "mdi:run-fast", None, False],
    "bodyBatteryChargedValue": [
        "Body Battery Charged",
        "%",
        "mdi:battery-charging-100",
        None,
        True,
    ],
    "bodyBatteryDrainedValue": [
        "Body Battery Drained",
        "%",
        "mdi:battery-alert-variant-outline",
        None,
        True,
    ],
    "bodyBatteryHighestValue": [
        "Body Battery Highest",
        "%",
        "mdi:battery-heart",
        None,
        True,
    ],
    "bodyBatteryLowestValue": [
        "Body Battery Lowest",
        "%",
        "mdi:battery-heart-outline",
        None,
        True,
    ],
    "bodyBatteryMostRecentValue": [
        "Body Battery Most Recent",
        "%",
        "mdi:battery-positive",
        None,
        True,
    ],
    "averageSpo2": ["Average SPO2", "%", "mdi:diabetes", None, True],
    "lowestSpo2": ["Lowest SPO2", "%", "mdi:diabetes", None, True],
    "latestSpo2": ["Latest SPO2", "%", "mdi:diabetes", None, True],
    "latestSpo2ReadingTimeLocal": [
        "Latest SPO2 Time",
        "",
        "mdi:diabetes",
        DEVICE_CLASS_TIMESTAMP,
        False,
    ],
    "averageMonitoringEnvironmentAltitude": [
        "Average Altitude",
        "%",
        "mdi:image-filter-hdr",
        None,
        False,
    ],
    "highestRespirationValue": [
        "Highest Respiration",
        "brpm",
        "mdi:progress-clock",
        None,
        False,
    ],
    "lowestRespirationValue": [
        "Lowest Respiration",
        "brpm",
        "mdi:progress-clock",
        None,
        False,
    ],
    "latestRespirationValue": [
        "Latest Respiration",
        "brpm",
        "mdi:progress-clock",
        None,
        False,
    ],
    "latestRespirationTimeGMT": [
        "Latest Respiration Update",
        "",
        "mdi:progress-clock",
        DEVICE_CLASS_TIMESTAMP,
        False,
    ],
    "weight": ["Weight", "kg", "mdi:weight-kilogram", None, False],
    "bmi": ["BMI", "", "mdi:food", None, False],
    "bodyFat": ["Body Fat", "%", "mdi:food", None, False],
    "bodyWater": ["Body Water", "%", "mdi:water-percent", None, False],
    "bodyMass": ["Body Mass", "kg", "mdi:food", None, False],
    "muscleMass": ["Muscle Mass", "kg", "mdi:dumbbell", None, False],
    "physiqueRating": ["Physique Rating", "", "mdi:numeric", None, False],
    "visceralFat": ["Visceral Fat", "", "mdi:food", None, False],
    "metabolicAge": ["Metabolic Age", "", "mdi:calendar-heart", None, False],
}
