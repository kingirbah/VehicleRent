# 📝 Template Update Guide - Quick Reference

## Files That Need Updates

This guide shows EXACTLY what to add to your existing HTML templates.

---

## 1. admin_add.html ⚠️ UPDATE NEEDED

### Location: After the `cc` field section

**ADD License Plate Field:**

```html
<!-- Add this right after the CC field -->
<div>
    <label class="block text-sm font-semibold text-gray-700 mb-2">
        License Plate Number
    </label>
    <input type="text" 
           name="license_plate" 
           placeholder="e.g., WXY 1234 or ABC 5678"
           class="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition uppercase">
    <p class="text-xs text-gray-500 mt-2">Optional - Will be automatically converted to uppercase</p>
</div>
```

### Location: Update the form tag

**CHANGE:**
```html
<form method="POST" class="space-y-6">
```

**TO:**
```html
<form method="POST" enctype="multipart/form-data" class="space-y-6">
```
☝️ This is CRITICAL for file upload to work!

### Location: Replace the "Image URL" section

**REPLACE the entire image URL section with:**

```html
<!-- Image Upload Section -->
<div class="border-t pt-6">
    <h3 class="text-lg font-bold text-gray-900 mb-4">📸 Vehicle Image</h3>
    
    <div class="space-y-4">
        <!-- Upload Option -->
        <div>
            <label class="block text-sm font-semibold text-gray-700 mb-2">
                Upload Image (Recommended)
            </label>
            <input type="file" 
                   name="image" 
                   accept="image/png, image/jpeg, image/jpg, image/webp"
                   class="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition">
            <div class="mt-2 space-y-1">
                <p class="text-xs text-gray-500">
                    ✅ Formats: PNG, JPG, JPEG, WEBP
                </p>
                <p class="text-xs text-gray-500">
                    📏 Max size: 1MB (will be auto-compressed if larger)
                </p>
                <p class="text-xs text-green-600">
                    💡 Best practice: Upload square images for optimal display
                </p>
            </div>
        </div>

        <!-- OR Divider -->
        <div class="relative">
            <div class="absolute inset-0 flex items-center">
                <div class="w-full border-t border-gray-300"></div>
            </div>
            <div class="relative flex justify-center text-sm">
                <span class="px-4 bg-white text-gray-500 font-semibold">OR</span>
            </div>
        </div>

        <!-- URL Option -->
        <div>
            <label class="block text-sm font-semibold text-gray-700 mb-2">
                Image URL (Alternative)
            </label>
            <input type="url" 
                   name="image_url" 
                   placeholder="https://example.com/image.jpg"
                   class="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition">
            <p class="text-xs text-gray-500 mt-2">Use this if you prefer to host the image elsewhere</p>
        </div>
    </div>
</div>
```

---

## 2. admin_edit.html ⚠️ UPDATE NEEDED

### Same changes as admin_add.html PLUS:

### Location: In the license plate field

**ADD this to show current value:**

```html
<input type="text" 
       name="license_plate" 
       value="{{ vehicle.license_plate or '' }}"
       placeholder="e.g., WXY 1234"
       class="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition uppercase">
```

### Location: In the image section

**ADD this to show current image:**

```html
<!-- Show current image if exists -->
{% if vehicle.image_url %}
<div class="mb-4 p-4 bg-gray-50 rounded-lg">
    <p class="text-sm font-semibold text-gray-700 mb-2">Current Image:</p>
    <img src="{{ vehicle.image_url }}" 
         alt="{{ vehicle.name }}" 
         class="w-32 h-32 object-cover rounded-lg border-2 border-gray-200">
</div>
{% endif %}
```

---

## 3. admin_detail.html ⚠️ UPDATE NEEDED

### Location: In the vehicle info section (top card)

**ADD license plate display:**

Find this section:
```html
<div class="flex items-center space-x-2 mb-2">
    <span class="inline-block px-2 py-1 bg-blue-100 text-blue-700 text-xs font-bold rounded uppercase">
        {{ vehicle.type }}
    </span>
    <span class="inline-block px-2 py-1 bg-gray-100 text-gray-700 text-xs font-bold rounded">
        {{ vehicle.cc }}CC
    </span>
</div>
```

**ADD after it:**
```html
<!-- License Plate Badge -->
{% if vehicle.license_plate %}
<span class="inline-block px-2 py-1 bg-yellow-100 text-yellow-700 text-xs font-bold rounded uppercase">
    🚗 {{ vehicle.license_plate }}
</span>
{% endif %}
```

### Location: In Add Booking Modal form

**ADD nationality field:**

Find the IC number field section, add AFTER it:

```html
<!-- Nationality Field -->
<div>
    <label class="block text-sm font-semibold text-gray-700 mb-2">Nationality</label>
    <select name="nationality" 
            class="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition">
        <option value="Malaysian" selected>Malaysian</option>
        <option value="Singaporean">Singaporean</option>
        <option value="Indonesian">Indonesian</option>
        <option value="Thai">Thai</option>
        <option value="Brunei">Brunei</option>
        <option value="Vietnamese">Vietnamese</option>
        <option value="Filipino">Filipino</option>
        <option value="Chinese">Chinese</option>
        <option value="Indian">Indian</option>
        <option value="Japanese">Japanese</option>
        <option value="Korean">Korean</option>
        <option value="Other">Other</option>
    </select>
    <p class="text-xs text-gray-500 mt-2">Customer's nationality for records</p>
</div>
```

### Location: In Edit Booking Modal form

**ADD nationality field with current value:**

```html
<!-- Nationality Field -->
<div>
    <label class="block text-sm font-semibold text-gray-700 mb-2">Nationality</label>
    <select name="nationality" 
            class="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition">
        <option value="Malaysian" {% if booking.nationality == 'Malaysian' %}selected{% endif %}>Malaysian</option>
        <option value="Singaporean" {% if booking.nationality == 'Singaporean' %}selected{% endif %}>Singaporean</option>
        <option value="Indonesian" {% if booking.nationality == 'Indonesian' %}selected{% endif %}>Indonesian</option>
        <option value="Thai" {% if booking.nationality == 'Thai' %}selected{% endif %}>Thai</option>
        <option value="Brunei" {% if booking.nationality == 'Brunei' %}selected{% endif %}>Brunei</option>
        <option value="Vietnamese" {% if booking.nationality == 'Vietnamese' %}selected{% endif %}>Vietnamese</option>
        <option value="Filipino" {% if booking.nationality == 'Filipino' %}selected{% endif %}>Filipino</option>
        <option value="Chinese" {% if booking.nationality == 'Chinese' %}selected{% endif %}>Chinese</option>
        <option value="Indian" {% if booking.nationality == 'Indian' %}selected{% endif %}>Indian</option>
        <option value="Japanese" {% if booking.nationality == 'Japanese' %}selected{% endif %}>Japanese</option>
        <option value="Korean" {% if booking.nationality == 'Korean' %}selected{% endif %}>Korean</option>
        <option value="Other" {% if booking.nationality == 'Other' %}selected{% endif %}>Other</option>
    </select>
</div>
```

### Location: In booking list display

**UPDATE booking display to show nationality:**

Find where bookings are displayed in the list and UPDATE to:

```html
<div class="text-sm text-gray-600">
    <strong>{{ b.customer_name }}</strong>
    {% if b.nationality %} • 🌍 {{ b.nationality }}{% endif %}
    {% if b.ic_number %}<br>IC: {{ b.ic_number }}{% endif %}
    {% if b.location %}<br>📍 {{ b.location }}{% endif %}
</div>
```

---

## 4. admin_catalog.html ⚠️ UPDATE NEEDED

### Location: In the navigation bar

**ADD link to All Bookings:**

Find the navigation section and ADD:

```html
<div class="flex items-center space-x-4">
    <a href="/admin/bookings" 
       class="text-sm text-gray-600 hover:text-blue-600 font-medium transition flex items-center space-x-1">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
        </svg>
        <span>All Bookings</span>
    </a>
    <a href="/" class="text-sm text-gray-600 hover:text-blue-600 font-medium transition">
        View Catalog
    </a>
    <a href="/logout" class="text-sm text-red-600 hover:text-red-700 font-semibold transition">
        Logout
    </a>
</div>
```

### Location: In vehicle card display

**ADD license plate badge:**

Find where vehicle info is shown:

```html
<div class="flex items-center space-x-2 mb-2">
    <span class="inline-block px-2 py-1 bg-blue-100 text-blue-700 text-xs font-bold rounded uppercase">
        {{ vehicle.type }}
    </span>
    <span class="inline-block px-2 py-1 bg-gray-100 text-gray-700 text-xs font-bold rounded">
        {{ vehicle.cc }}CC
    </span>
    <!-- ADD THIS -->
    {% if vehicle.license_plate %}
    <span class="inline-block px-2 py-1 bg-yellow-100 text-yellow-700 text-xs font-bold rounded uppercase">
        {{ vehicle.license_plate }}
    </span>
    {% endif %}
</div>
```

---

## 5. Error Pages (Optional but Recommended)

### Create templates/404.html

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>404 - Page Not Found</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50 flex items-center justify-center min-h-screen">
    <div class="text-center">
        <h1 class="text-9xl font-bold text-blue-600">404</h1>
        <h2 class="text-3xl font-bold text-gray-900 mt-4">Page Not Found</h2>
        <p class="text-gray-600 mt-2 mb-8">The page you're looking for doesn't exist.</p>
        <a href="/admin" class="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-semibold transition">
            Go to Admin Panel
        </a>
    </div>
</body>
</html>
```

### Create templates/500.html

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>500 - Server Error</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50 flex items-center justify-center min-h-screen">
    <div class="text-center">
        <h1 class="text-9xl font-bold text-red-600">500</h1>
        <h2 class="text-3xl font-bold text-gray-900 mt-4">Server Error</h2>
        <p class="text-gray-600 mt-2 mb-8">Something went wrong. Please try again later.</p>
        <a href="/admin" class="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-semibold transition">
            Go to Admin Panel
        </a>
    </div>
</body>
</html>
```

---

## ✅ Validation Checklist

After making updates, test these:

### License Plate:
- [ ] Can add vehicle with license plate
- [ ] Can add vehicle without license plate (optional)
- [ ] Duplicate plate shows error
- [ ] Plate auto-converts to uppercase
- [ ] Plate shows on all vehicle displays

### Image Upload:
- [ ] Can upload PNG file
- [ ] Can upload JPG file
- [ ] Can upload WEBP file
- [ ] Large image gets compressed
- [ ] Can still use URL instead
- [ ] Old image deleted when updating

### Nationality:
- [ ] Shows in add booking form
- [ ] Shows in edit booking form
- [ ] Defaults to "Malaysian"
- [ ] Displays in booking details
- [ ] Searchable in all bookings

### All Bookings:
- [ ] Page loads at /admin/bookings
- [ ] Filters work correctly
- [ ] Search works
- [ ] Sorting works
- [ ] Statistics accurate
- [ ] Print opens new window
- [ ] Print report looks good

---

## 🚨 Common Issues & Fixes

### Issue: "enctype not set" - File upload fails
**Fix:** Add `enctype="multipart/form-data"` to form tag

### Issue: Images not showing
**Fix:** Check path starts with `/static/` not `static/`

### Issue: License plate not uppercase
**Fix:** Add `class="uppercase"` to input OR use `.upper()` in Python

### Issue: Nationality not saving
**Fix:** Check field name is exactly `nationality` in form AND route

### Issue: Print button does nothing
**Fix:** Check route has proper filters in URL parameters

---

## 📦 Quick Copy-Paste Nationality Options

```html
<option value="Malaysian">Malaysian</option>
<option value="Singaporean">Singaporean</option>
<option value="Indonesian">Indonesian</option>
<option value="Thai">Thai</option>
<option value="Brunei">Brunei</option>
<option value="Vietnamese">Vietnamese</option>
<option value="Filipino">Filipino</option>
<option value="Chinese">Chinese</option>
<option value="Indian">Indian</option>
<option value="Japanese">Japanese</option>
<option value="Korean">Korean</option>
<option value="Australian">Australian</option>
<option value="British">British</option>
<option value="American">American</option>
<option value="Other">Other</option>
```

---

**Last Updated**: February 6, 2026  
**Version**: 6.0  
**Status**: Ready to implement ✅
