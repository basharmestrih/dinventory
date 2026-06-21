TRANSLATIONS = {
    "ar": {
        "messages": {
            "welcome": (
                "📌 دليل سريع:\n"
                "1. اضغط على \"🛍️ شراء\".\n"
                "2. اختر المنتج الذي تريده.\n"
                "3. أكمل عملية الدفع.\n"
                "4. بعد الدفع، أرسل رقم العملية (TXID) أو رقم الطلب هنا للتحقق.\n\n"
                "📌 يرجى اختيار من القائمة :)"
            ),
            "menu_prompt": "اختر من القائمة",
        },
        "buttons": {
            "buy": "🛍️ شراء",
            "buy_now": "اشتر الآن",
            "profile": "👤 الملف الشخصي",
            "purchase_history": "📜 سجل المشتريات",
            "wallet": "💼 المحفظة",
            "support": "🛠️ الدعم",
            "api_link": "🔗 رابط API",
            "dashboard": "لوحة التحكم",
            "back_to_menu": "الرجوع للقائمة",
            "back_to_dashboard": "الرجوع للوحة التحكم",
            "contact_support_telegram_button": "تليجرام",
            "contact_support_whatsapp_button": "واتساب",
            "set_special_products": "تحديد المنتجات المميزة",
        },
        "sections": {
            "buy": "🛍️ قسم الشراء: هنا يمكنك تصفح المنتجات الرقمية المتاحة للشراء.",
            "profile": "👤 قسم الملف الشخصي: هنا ستظهر بيانات حساب المستخدم.",
            "purchase_history": "📜 قسم سجل المشتريات: هنا ستظهر الطلبات السابقة للمستخدم.",
            "wallet": "💼 قسم المحفظة: هنا ستظهر معلومات الرصيد وطرق الدفع.",
            "support": "🛠️ قسم الدعم: يمكنك مراسلتنا لأي استفسار تقني أو أي مشكلة أخرى، وسنساعدك في أقرب وقت.",
            "api_link": "🔗 قسم رابط API: هنا يمكن عرض الرابط أو معلومات التكامل.",
            "no_products": "لا توجد منتجات متاحة حاليا.",
            "products_load_failed": "حدث خطأ أثناء جلب المنتجات. حاول مرة أخرى.",
            "supabase_not_configured": "لم يتم إعداد اتصال Supabase بعد. أضف بياناته في ملف .env.",
            "product_selected": "تم اختيار المنتج.",
            "product_not_found": "هذا المنتج غير موجود أو تم حذفه.",
            "product_unavailable_support": (
                "هذا المنتج غير متوفر حاليا.\n\n"
                "يرجى التواصل مع الدعم عبر واتساب أو تليجرام."
            ),
        },
        "purchase": {
            "selected_product": (
                "✨🤖المنتج:  {title}\n\n"
                "📝 التفاصيل:\n"
                "{description}\n"
                "💰 السعر:\n"
                "{price} جنيه مصري\n\n"
                "📦 الكمية المتوفرة:\n"
                "{quantity} حساب\n\n"
                "ادخل الكمية المطلوبة (مثال: 1 , 5)"
            ),
            "product_out_of_stock": "هذا المنتج غير متوفر حاليا.",
            "invalid_quantity": "أرسل كمية صحيحة من 1 إلى {max_quantity}.",
            "ask_duration": "اختر مدة الاشتراك:",
            "ask_assignment_email": "أرسل الآن البريد الإلكتروني الشخصي الذي سيتم تفعيل الحساب عليه.",
            "invalid_assignment_email": "أرسل بريدا إلكترونيا صحيحا.",
            "choose_payment_method": "الكمية: {quantity}\nالإجمالي: {total} جنيه مصري\n\nاختر طريقة الدفع:",
            "duration_buttons": {
                "one_month": "شهر واحد\n25 جنيه مصري",
                "two_months": "شهرين\n40 جنيه مصري",
                "six_months": "6 أشهر\n100 جنيه مصري",
                "twelve_months": "12 شهر\n350 جنيه مصري",
            },
            "buttons": {
                "wallet": "محفظتي",
                "ewallet": "محفظة الموبايل",
                "fawry": "فوري",
                "instapay": "انستا باي",
                "binance": "بينانس",
            },
            "instapay_instructions": "أرسل المبلغ {total} جنيه مصري عبر InstaPay إلى رقم الهاتف:\n{phone_number}\n\nبعد التحويل، أرسل صورة Screenshot لإثبات الدفع هنا.",
            "instapay_ask_for_amount": "أدخل المبلغ المراد إرساله بالجنيه المصري",
            "deposit_instapay_instructions": "أرسل المبلغ  بالجنيه مصري عبر InstaPay إلى رقم الهاتف:\n{phone_number}\n\nبعد التحويل، أرسل صورة Screenshot لإثبات الدفع هنا.",
            "payment_method_disabled": "هذه الطريقة غير مفعلة حاليا.",
            "wallet_coming_soon": "المحفظة ستعمل قريباً.",
            "ewallet_coming_soon": "المحفظة الالكترونية ستعمل قريباً.",
            "invalid_transaction_id": "أرسل رقم عملية صحيح بعد إتمام الدفع.",
            "order_create_failed": "حدث خطأ أثناء حفظ الطلب. حاول مرة أخرى.",
            "order_create_failed_with_reason": "حدث خطأ أثناء حفظ الطلب:\n{reason}",
            "order_under_review": "تم استلام رقم العملية: {transaction_id}\n\nسيقوم الأدمن بمراجعة الطلب، وسيتم إكمال الـ checkout لاحقا بعد التأكيد.",
            "order_not_found": "الطلب غير موجود.",
            "order_already_processed": "تمت مراجعة هذا الطلب مسبقا.",
            "order_status_updated": "تم تحديث حالة الطلب.",
            "review_approve_button": "موافقة",
            "review_approve_with_note_button": "موافقة مع ملاحظة",
            "review_reject_button": "رفض",
            "ask_review_note": "أرسل الآن الملاحظة التي تريد إرسالها للمستخدم.",
            "review_note_empty": "أرسل نص ملاحظة صالح.",
            "order_stock_update_failed": "حدث خطأ أثناء تحديث كمية المنتج.",
            "order_product_not_found": "المنتج المرتبط بهذا الطلب غير موجود.",
            "order_insufficient_stock": "لا توجد كمية كافية لإكمال الطلب. الكمية المتاحة حاليا: {available_quantity}",
            "order_credentials_unavailable": "لا توجد بيانات دخول متاحة لهذا المنتج حاليا.",
            "adobe_order_credentials_unavailable": "المنتج غير متوفر من المزود",
            "order_credentials_failed": "حدث خطأ أثناء تجهيز بيانات الدخول للطلب.",
            "order_paid_to_user": "تم إكمال الطلب رقم {order_id} بنجاح.{order_action_line}",
            "order_paid_manual_activation": "تم تأكيد طلبك رقم {order_id} بنجاح.\n\nسيقوم فريق الإدارة بتفعيل الحسابات على البريد الإلكتروني الذي أرسلته في أقرب وقت ممكن.",
            "order_activation_pending_to_user": (
                "تم تأكيد الدفع للطلب رقم {order_id} بنجاح.\n\n"
                "تم استلام طلبك وسيتم معالجته من قبل فريق الإدارة قريباً."
            ),
            "order_activation_rejected_to_user": (
                "لم يتم تفعيل طلبك رقم {order_id}.\n\n"
                "إذا كنت تحتاج مساعدة أو تريد متابعة المشكلة، تواصل مع الدعم."
            ),
            "order_credentials_message": "بيانات طلبك:\n\n{credentials}",
            "order_credential_item": "الحساب {index}\nEmail: {email}\nPassword: {password}",
            "order_review_note_message": "ملاحظة من الإدارة:\n\n{note}",
            "order_rejected_to_user": "لم يتم إكمال طلبك رقم {order_id}.\n\nإذا كنت تحتاج مساعدة أو تريد متابعة المشكلة، تواصل مع الدعم.",
            "ask_activation_note": "أرسل الآن الملاحظة التي تريد إرسالها للمستخدم.",
            "activation_activate_button": "تفعيل",
            "activation_activate_with_note_button": "تفعيل مع ملاحظة",
            "activation_reject_button": "رفض",
            "contact_support_button": "التواصل مع الدعم",
            "admin_order_notification": "طلب جديد بانتظار المراجعة\n\nرقم الطلب: {order_id}\nالمنتج: {product_title}\nالكمية: {quantity}\nالإجمالي: {total}\nطريقة الدفع: {payment_method}\n\nبيانات العميل:\nالاسم: {customer_name}\nاليوزر: {customer_username}\nالآيدي: {customer_id}{activation_emails_block}",
            "admin_activation_emails_block": "\n\nالإيميلات المطلوبة للتفعيل:\n{emails}",
            "admin_adobe_assignment_block": "\n\nبريد Adobe للتفعيل: {email}\nمدة الاشتراك: {duration}",
            "ask_activation_emails": "أرسل الآن عدد {quantity} من الإيميلات، كل إيميل في سطر منفصل.",
            "invalid_activation_emails_count": "عدد الإيميلات يجب أن يساوي الكمية المطلوبة.\nالكمية: {quantity}\nعدد الإيميلات: {emails_count}",
        },
        "profile": {
            "username_missing": "حسابك في تيليجرام لا يحتوي على اسم مستخدم. أضف username ثم أعد المحاولة.",
            "load_failed": "حدث خطأ أثناء جلب بيانات الملف الشخصي.",
            "load_failed_with_reason": "حدث خطأ أثناء جلب بيانات الملف الشخصي:\n{reason}",
            "not_found": "لم يتم العثور على بيانات للمستخدم: @{username}",
            "details": "📄 بيانات الملف الشخصي:\n 👤 اسم المستخدم: {username}\n💰 إجمالي الإنفاق: {total_spent} جنيه مصري\n🧾 آخر طلب: {last_spent_order}\n", },
        "history": {
            "username_missing": "حسابك في تيليجرام لا يحتوي على اسم مستخدم. أضف username ثم أعد المحاولة.",
            "load_failed": "حدث خطأ أثناء جلب سجل المشتريات.",
            "load_failed_with_reason": "حدث خطأ أثناء جلب سجل المشتريات:\n{reason}",
            "no_paid_orders": "لا توجد طلبات مدفوعة للمستخدم: @{username}",
            "title": "سجل الطلبات المدفوعة للمستخدم @{username}\nعدد الطلبات: {count}",
            "order_item": "رقم الطلب: {order_id}\nالمنتج: {product_title}\nالكمية: {quantity}\nالإجمالي: {total}\nطريقة الدفع: {payment_method}\nتاريخ التأكيد: {created_at}",
        },
        "wallet": {
            "username_missing": "حسابك في تيليجرام لا يحتوي على اسم مستخدم. أضف username ثم أعد المحاولة.",
            "load_failed": "حدث خطأ أثناء جلب بيانات المحفظة.",
            "load_failed_with_reason": "حدث خطأ أثناء جلب بيانات المحفظة:\n{reason}",
            "not_found": "لم يتم العثور على محفظة للمستخدم: @{username}",
            "details": "بيانات المحفظة:\nاسم المستخدم: @{username}\nالرصيد: {balance_egp} جنيه مصري\nآخر إيداع: {last_deposit_at}\n\nاختر طريقة الإيداع:",
            "ask_binance_amount": "Ø£Ø±Ø³Ù„ Ù‚ÙŠÙ…Ø© Ø§Ù„Ø¥ÙŠØ¯Ø§Ø¹ Ø¨Ø§Ù„Ø¯ÙˆÙ„Ø§Ø±.",
            "ask_instapay_amount": "Ø£Ø±Ø³Ù„ Ù‚ÙŠÙ…Ø© Ø§Ù„Ø¥ÙŠØ¯Ø§Ø¹ Ø¨Ø§Ù„Ø¬Ù†ÙŠÙ‡ Ø§Ù„Ù…ØµØ±ÙŠ.",
            "invalid_amount": "Ø£Ø±Ø³Ù„ Ù…Ø¨Ù„ØºØ§ ØµØ­ÙŠØ­Ø§ Ø£ÙƒØ¨Ø± Ù…Ù† ØµÙØ±.",
            "invalid_transaction_id": "Ø£Ø±Ø³Ù„ Ø±Ù‚Ù… Ø¹Ù…Ù„ÙŠØ© ØµØ­ÙŠØ­ Ø¨Ø¹Ø¯ Ø¥ØªÙ…Ø§Ù… Ø§Ù„Ø¥ÙŠØ¯Ø§Ø¹.",
            "invalid_topup_method": "Ø·Ø±ÙŠÙ‚Ø© Ø§Ù„Ø¥ÙŠØ¯Ø§Ø¹ ØºÙŠØ± ØµØ­ÙŠØ­Ø©.",
            "ewallet_coming_soon": "Ø§Ù„Ø¥ÙŠØ¯Ø§Ø¹ Ø¹Ø¨Ø± E-Wallet Ø³ÙŠØªÙˆÙØ± Ù‚Ø±ÙŠØ¨Ø§Ù‹.",
            "topup_under_review": "ØªÙ… Ø§Ø³ØªÙ„Ø§Ù… Ø·Ù„Ø¨ Ø§Ù„Ø¥ÙŠØ¯Ø§Ø¹ Ø¨Ø±Ù‚Ù… Ø§Ù„Ø¹Ù…Ù„ÙŠØ©: {transaction_id}\n\nØ³ÙŠØ±Ø§Ø¬Ø¹ Ø§Ù„Ø£Ø¯Ù…Ù† Ø§Ù„Ø·Ù„Ø¨ ÙˆØ¹Ù†Ø¯ Ø§Ù„Ù…ÙˆØ§ÙÙ‚Ø© Ø³ÙŠØªÙ… Ø¥Ø¶Ø§ÙØ© Ø§Ù„Ø±ØµÙŠØ¯ Ø¥Ù„Ù‰ Ù…Ø­ÙØ¸ØªÙƒ.",
            "admin_topup_notification": "Ø·Ù„Ø¨ Ø¥ÙŠØ¯Ø§Ø¹ Ù…Ø­ÙØ¸Ø© Ø¬Ø¯ÙŠØ¯\n\nØ§Ù„Ù…Ø³ØªØ®Ø¯Ù…: @{username}\nØ§Ù„Ù…Ø¨Ù„Øº: {amount} {currency}\nØ·Ø±ÙŠÙ‚Ø© Ø§Ù„Ø¥ÙŠØ¯Ø§Ø¹: {payment_method}\nØ±Ù‚Ù… Ø§Ù„Ø¹Ù…Ù„ÙŠØ©: {transaction_id}\nØ§Ù„Ø­Ø§Ù„Ø©: {status}\n\nØ¨ÙŠØ§Ù†Ø§Øª Ø§Ù„Ø¹Ù…ÙŠÙ„:\nØ§Ù„Ø§Ø³Ù…: {customer_name}\nØ§Ù„ÙŠÙˆØ²Ø±: {customer_username}\nØ§Ù„Ø¢ÙŠØ¯ÙŠ: {customer_id}",
            "review_approve_button": "Ù…ÙˆØ§ÙÙ‚Ø©",
            "review_reject_button": "Ø±ÙØ¶",
            "request_not_found": "Ø·Ù„Ø¨ Ø§Ù„Ø¥ÙŠØ¯Ø§Ø¹ ØºÙŠØ± Ù…ÙˆØ¬ÙˆØ¯.",
            "request_already_processed": "ØªÙ…Øª Ù…Ø¹Ø§Ù„Ø¬Ø© Ø·Ù„Ø¨ Ø§Ù„Ø¥ÙŠØ¯Ø§Ø¹ Ù…Ø³Ø¨Ù‚Ø§.",
            "request_approved": "ØªÙ… Ø§Ù„Ù…ÙˆØ§ÙÙ‚Ø© Ø¹Ù„Ù‰ Ø·Ù„Ø¨ Ø§Ù„Ø¥ÙŠØ¯Ø§Ø¹.",
            "request_rejected": "ØªÙ… Ø±ÙØ¶ Ø·Ù„Ø¨ Ø§Ù„Ø¥ÙŠØ¯Ø§Ø¹.",
            "topup_apply_failed": "Ø­Ø¯Ø« Ø®Ø·Ø£ Ø£Ø«Ù†Ø§Ø¡ Ø¥Ø¶Ø§ÙØ© Ø§Ù„Ø±ØµÙŠØ¯ Ø¥Ù„Ù‰ Ø§Ù„Ù…Ø­ÙØ¸Ø©.",
            "topup_approved_to_user": "ØªÙ…Øª Ø§Ù„Ù…ÙˆØ§ÙÙ‚Ø© Ø¹Ù„Ù‰ Ø¥ÙŠØ¯Ø§Ø¹Ùƒ Ø¨Ù…Ø¨Ù„Øº {amount} {currency} Ø¹Ø¨Ø± {payment_method}.\nØ±ØµÙŠØ¯Ùƒ Ø§Ù„Ø­Ø§Ù„ÙŠ: {balance} {currency}",
            "topup_rejected_to_user": "ØªÙ… Ø±ÙØ¶ Ø·Ù„Ø¨ Ø¥ÙŠØ¯Ø§Ø¹Ùƒ Ø¨Ù…Ø¨Ù„Øº {amount} {currency} Ø¹Ø¨Ø± {payment_method}. Ø¥Ø°Ø§ ÙƒÙ†Øª ØªØ­ØªØ§Ø¬ Ù…Ø³Ø§Ø¹Ø¯Ø© ØªÙˆØ§ØµÙ„ Ù…Ø¹ Ø§Ù„Ø¯Ø¹Ù….",
            "buttons": {
                "ewallet": "محفظة آلي",
                "binance": "بينانس",
                "instapay": "انستا باي"
            }
        },
        "dashboard": {
            "buttons": {
                "products_management": "ادارة المنتجات",
                "broadcast_management": "ارسال الاشعارات",
                "payment_methods": "طرق الدفع",
                "sales_reports": "تقارير البيع",
                "add_product": "إضافة منتج",
                "edit_product": "تعديل منتج",
                "delete_product": "حذف منتج",
                "edit_name": "تعديل الاسم",
                "edit_description": "تعديل الوصف",
                "edit_quantity": "تعديل الكمية",
                "edit_supplier_price": "تعديل سعر المورد",
                "edit_price": "تعديل سعر البيع",
                "finish_editing": "إنهاء التعديل",
                "broadcast_notification": "إرسال إشعار للجميع",
                "wallet_method": "المحفظة",
                "e_wallet": "محفظة الكترونية",
                "fawry_method": "فوري",
                "instapay_method": "انستاباي",
                "binance_method": "بينانس",
                "enable": "تفعيل",
                "disable": "تعطيل",
                "enabled": "مفعل",
                "disabled": "معطل",
                "credentials_yes": "نعم",
                "credentials_no": "لا",
                "enabled_icon": "✅",
                "disabled_icon": "❌",
                "status_label": "الحالة",
                "export_products": "تصدير المنتجات Excel",
                "export_product_revenue": "تصدير أرباح المنتجات Excel",
                "export_payment_method_usage": "تصدير طرق الدفع Excel",
                "export_daily_revenue": "تصدير الإيراد اليومي Excel",
                "export_users": "تصدير المستخدمين Excel",
                "export_orders": "تصدير الطلبات Excel",
                "export_wallet_topups": "عمليات الايداع",
            },
            "messages": {
                "welcome": "لوحة التحكم. اختر القسم الذي تريد إدارته.",
                "access_denied": "ليس لديك صلاحية للوصول إلى لوحة التحكم.",
                "products_section": "قسم ادارة المنتجات.",
                "notifications_section": "قسم ارسال الاشعارات.",
                "payment_methods_section": "قسم طرق الدفع.",
                "sales_section": "قسم تقارير البيع.",
                "payment_method_status_updated": "تم تحديث حالة طريقة الدفع.",
                "product_created": "تمت إضافة المنتج بنجاح.",
                "product_updated": "تم تحديث المنتج بنجاح.",
                "product_deleted": "تم حذف المنتج بنجاح.",
                "broadcast_prompt": "أرسل الآن نص الإشعار الذي تريد إرساله إلى جميع مستخدمي البوت.",
                "broadcast_empty": "أرسل نصا صالحا للإشعار.",
                "broadcast_success": "تم إرسال الإشعار إلى {success_count} مستخدم من أصل {total_recipients}. تعذر الإرسال إلى {failed_count} مستخدم.",
                "broadcast_failed": "حدث خطأ أثناء إرسال الإشعار.",
                "broadcast_failed_with_reason": "حدث خطأ أثناء إرسال الإشعار:\n{reason}",
                "create_failed": "حدث خطأ أثناء إضافة المنتج.",
                "create_failed_with_reason": "حدث خطأ أثناء إضافة المنتج:\n{reason}",
                "update_failed": "حدث خطأ أثناء تحديث المنتج.",
                "update_failed_with_reason": "حدث خطأ أثناء تحديث المنتج:\n{reason}",
                "delete_failed": "حدث خطأ أثناء حذف المنتج.",
                "delete_failed_with_reason": "حدث خطأ أثناء حذف المنتج:\n{reason}",
                "export_failed": "حدث خطأ أثناء تجهيز ملف المنتجات.",
                "export_failed_with_reason": "حدث خطأ أثناء تجهيز ملف التصدير:\n{reason}",
                "export_ready": "تم تجهيز ملف المنتجات.",
                "select_for_edit": "اختر المنتج الذي تريد تعديله.",
                "select_for_delete": "اختر المنتج الذي تريد حذفه.",
                "edit_menu": "اختر ما تريد تعديله في المنتج:\n\nالاسم: {title}\nالوصف: {description}\nالكمية: {quantity}\nسعر المورد: {supplier_price}\nسعر البيع: {price}",
                "no_product_revenue": "لا توجد بيانات في جدول أرباح المنتجات.",
                "no_payment_method_usage": "لا توجد بيانات في جدول طرق الدفع.",
                "no_daily_revenue": "لا توجد بيانات في جدول الإيراد اليومي.",
                "no_users": "لا توجد بيانات في جدول المستخدمين.",
                "no_orders": "لا توجد بيانات في جدول الطلبات.",
                "no_wallet_topups": "لا توجد بيانات في جدول عمليات الإيداع.",
            },
            "add": {
                "ask_title": "أرسل عنوان المنتج.",
                "ask_description": "أرسل وصف المنتج.",
                "ask_quantity": "أرسل الكمية المتاحة.",
                "ask_supplier_price": "أرسل سعر المورد.",
                "ask_price": "أرسل سعر البيع.",
                "ask_credentials_required": "هل هذا المنتج يحتاج إدخال credentials؟",
                "ask_credentials": "أرسل credentials بهذا الشكل، كل حساب في سطر:\nemail@example.com | password",
            },
            "edit": {
                "ask_title": "أرسل الاسم الجديد.\nالحالي: {current}",
                "ask_description": "أرسل الوصف الجديد.\nالحالي: {current}",
                "ask_quantity": "أرسل الكمية الجديدة.\nالحالي: {current}",
                "ask_supplier_price": "أرسل سعر المورد الجديد.\nالحالي: {current}",
                "ask_price": "أرسل سعر البيع الجديد.\nالحالي: {current}",
            },
            "validation": {
                "invalid_quantity": "أرسل كمية صحيحة أكبر من صفر.",
                "invalid_price": "أرسل سعرا صحيحا يساوي صفر أو أكبر.",
                "invalid_quantity_or_skip": "أرسل كمية صحيحة أكبر من صفر.",
                "invalid_price_or_skip": "أرسل سعرا صحيحا.",
                "invalid_edit_text": "أرسل نصا صالحا.",
                "choose_credentials_option": "اختر نعم أو لا من الأزرار.",
                "invalid_credentials_format": "صيغة credentials غير صحيحة. أرسل كل حساب في سطر بهذا الشكل:\nemail@example.com | password",
                "credentials_count_mismatch": "عدد credentials يجب أن يساوي الكمية.\nالكمية: {quantity}\nعدد credentials: {credentials_count}",
            },
        },
    }
}

TRANSLATIONS["ar"]["purchase"]["order_paid_manual_activation"] = (
    "تم تأكيد طلبك رقم {order_id} بنجاح.\n\n"
    "تم تفعيل بريدك الإلكتروني بنجاح. يرجى التحقق من Gmail والبحث عن رسالة التفعيل المرسلة من Adobe.{order_action_line}"
)

TRANSLATIONS["ar"]["dashboard"]["buttons"]["change_order_approved_message"] = "Edit order approve message"
TRANSLATIONS["ar"]["dashboard"]["buttons"]["change_order_rejected_message"] = "Edit order reject message"
TRANSLATIONS["ar"]["dashboard"]["buttons"]["change_wallet_topup_approved_message"] = "Edit wallet top-up approve message"
TRANSLATIONS["ar"]["dashboard"]["buttons"]["change_wallet_topup_rejected_message"] = "Edit wallet top-up reject message"
TRANSLATIONS["ar"]["dashboard"]["messages"]["ask_review_message"] = (
    "Send the new message text.\n\n"
    "Current message:\n{current_message}\n\n"
    "Available placeholders:\n{placeholders}"
)
TRANSLATIONS["ar"]["dashboard"]["messages"]["invalid_review_message"] = "Send a valid message."
TRANSLATIONS["ar"]["dashboard"]["messages"]["review_message_updated"] = "Message updated successfully."
TRANSLATIONS["ar"]["purchase"]["binance_instructions"] = (
    "أرسل ما يعادل {total} جنيه مصري عبر Binance Pay.\n"
    "المبلغ بالدولار: {usd_total}$\n"
    "سعر الصرف الحالي: {exchange_rate} جنيه لكل 1$\n"
    "Binance ID: {binance_id}\n\n"
    "بعد التحويل، أرسل رقم العملية أو Transaction ID هنا."
)

TRANSLATIONS["ar"]["dashboard"]["buttons"]["other"] = "اخرى"
TRANSLATIONS["ar"]["dashboard"]["buttons"]["change_egp_exchange_rate"] = "تغيير سعر صرف الجنيه"
TRANSLATIONS["ar"]["dashboard"]["buttons"]["adjust_wallet_balance"] = "إضافة / خصم رصيد"
TRANSLATIONS["ar"]["dashboard"]["buttons"]["add_balance"] = "إضافة رصيد"
TRANSLATIONS["ar"]["dashboard"]["buttons"]["cut_balance"] = "خصم رصيد"
TRANSLATIONS["ar"]["dashboard"]["messages"]["other_section"] = "قسم الإعدادات الأخرى."
TRANSLATIONS["ar"]["dashboard"]["messages"]["ask_egp_exchange_rate"] = (
    "أرسل الآن سعر صرف الجنيه الجديد.\n"
    "السعر الحالي: {current_rate}\n"
    "السعر الافتراضي: {default_rate}"
)
TRANSLATIONS["ar"]["dashboard"]["messages"]["invalid_egp_exchange_rate"] = (
    "أرسل سعر صرف صحيحا أكبر من صفر."
)
TRANSLATIONS["ar"]["dashboard"]["messages"]["egp_exchange_rate_updated"] = (
    "تم تحديث سعر صرف الجنيه بنجاح.\n"
    "السعر السابق: {old_rate}\n"
    "السعر الجديد: {new_rate}"
)
TRANSLATIONS["ar"]["dashboard"]["messages"]["ask_special_products"] = (
    "اختر المنتجات المميزة عبر أرقامها، مفصولة بمسافة أو فاصلة.\n\n"
    "{products_list}"
)
TRANSLATIONS["ar"]["dashboard"]["messages"]["ask_wallet_user"] = "اختر المستخدم الذي تريد تعديل رصيده:"
TRANSLATIONS["ar"]["dashboard"]["messages"]["wallet_users_load_failed"] = "حدث خطأ أثناء جلب مستخدمي المحفظة."
TRANSLATIONS["ar"]["dashboard"]["messages"]["wallet_users_load_failed_with_reason"] = (
    "حدث خطأ أثناء جلب مستخدمي المحفظة:\n{reason}"
)
TRANSLATIONS["ar"]["dashboard"]["messages"]["no_wallet_users"] = "لا توجد محافظ متاحة حاليًا."
TRANSLATIONS["ar"]["dashboard"]["messages"]["ask_wallet_action"] = (
    "المستخدم: @{username}\n"
    "الرصيد الحالي: {balance} جنيه مصري\n\n"
    "اختر العملية المطلوبة:"
)
TRANSLATIONS["ar"]["dashboard"]["messages"]["ask_wallet_balance_amount"] = (
    "اختر رصيد المستخدم @{username} ثم أرسل المبلغ المطلوب لتنفيذ عملية {action}."
)
TRANSLATIONS["ar"]["dashboard"]["messages"]["invalid_wallet_balance_amount"] = "أرسل مبلغًا صحيحًا أكبر من صفر."
TRANSLATIONS["ar"]["dashboard"]["messages"]["wallet_balance_update_failed"] = "حدث خطأ أثناء تعديل الرصيد."
TRANSLATIONS["ar"]["dashboard"]["messages"]["wallet_balance_update_failed_with_reason"] = (
    "حدث خطأ أثناء تعديل الرصيد:\n{reason}"
)
TRANSLATIONS["ar"]["dashboard"]["messages"]["wallet_balance_updated"] = (
    "تم تنفيذ عملية {action} بنجاح للمستخدم @{username}.\n"
    "المبلغ: {amount} جنيه مصري\n"
    "الرصيد الحالي: {balance} جنيه مصري"
)
TRANSLATIONS["ar"]["dashboard"]["messages"]["wallet_balance_context_lost"] = (
    "تعذر تحديد المستخدم أو العملية. ابدأ العملية من جديد."
)
TRANSLATIONS["ar"]["dashboard"]["messages"]["invalid_special_products_selection"] = (
    "أرسل أرقام صحيحة فقط، مفصولة بمسافة أو فاصلة."
)
TRANSLATIONS["ar"]["dashboard"]["messages"]["special_products_updated"] = (
    "تم تحديث المنتجات المميزة بنجاح.\n"
    "عدد المنتجات المحددة: {updated_count}\n"
    "المنتجات: {selected_items}"
)

TRANSLATIONS["ar"]["purchase"]["order_credential_item"] = "{email} | {password}"

TRANSLATIONS["ar"]["purchase"]["invalid_instapay_screenshot"] = (
    "أرسل صورة Screenshot صحيحة لإثبات دفع InstaPay."
)
TRANSLATIONS["ar"]["purchase"]["order_under_review_with_screenshot"] = (
    "تم استلام صورة إثبات الدفع.\n\n"
    "سيقوم الأدمن بمراجعة الطلب، وسيتم إكمال العملية لاحقا بعد التأكيد."
)
TRANSLATIONS["ar"]["purchase"]["instapay_screenshot_reference"] = "مرفق Screenshot لإثبات الدفع"
TRANSLATIONS["ar"]["dashboard"]["buttons"]["change_instapay_phone_number"] = "تغيير رقم InstaPay"
TRANSLATIONS["ar"]["dashboard"]["buttons"]["change_binance_id"] = "تغيير Binance ID"
TRANSLATIONS["ar"]["dashboard"]["buttons"]["change_support_username"] = "تغيير يوزر الدعم"
TRANSLATIONS["ar"]["dashboard"]["buttons"]["change_support_whatsapp_phone"] = "تغيير رقم الواتساب"
TRANSLATIONS["ar"]["dashboard"]["messages"]["ask_instapay_phone_number"] = (
    "أرسل رقم InstaPay الجديد.\n"
    "الرقم الحالي: {current_phone_number}"
)
TRANSLATIONS["ar"]["dashboard"]["messages"]["invalid_instapay_phone_number"] = (
    "أرسل رقم InstaPay صحيحاً، مثال: +201234567890"
)
TRANSLATIONS["ar"]["dashboard"]["messages"]["instapay_phone_number_updated"] = (
    "تم تحديث رقم InstaPay بنجاح.\n"
    "الرقم السابق: {old_phone_number}\n"
    "الرقم الجديد: {new_phone_number}"
)
TRANSLATIONS["ar"]["dashboard"]["messages"]["ask_binance_id"] = (
    "أرسل Binance ID الجديد.\n"
    "القيمة الحالية: {current_binance_id}"
)
TRANSLATIONS["ar"]["dashboard"]["messages"]["invalid_binance_id"] = (
    "أرسل Binance ID صحيحاً (أرقام فقط)."
)
TRANSLATIONS["ar"]["dashboard"]["messages"]["binance_id_updated"] = (
    "تم تحديث Binance ID بنجاح.\n"
    "القيمة السابقة: {old_binance_id}\n"
    "القيمة الجديدة: {new_binance_id}"
)
TRANSLATIONS["ar"]["dashboard"]["messages"]["ask_support_username"] = (
    "أرسل يوزر الدعم الجديد (بدون @).\n"
    "القيمة الحالية: @{current_support_username}"
)
TRANSLATIONS["ar"]["dashboard"]["messages"]["ask_support_whatsapp_phone"] = (
    "أرسل رقم الواتساب الجديد.\n"
    "الرقم الحالي: {current_whatsapp_phone}"
)
TRANSLATIONS["ar"]["dashboard"]["messages"]["invalid_support_whatsapp_phone"] = (
    "أرسل رقم واتساب صحيحاً، مثال: +963937138915"
)
TRANSLATIONS["ar"]["dashboard"]["messages"]["support_whatsapp_phone_updated"] = (
    "تم تحديث رقم الواتساب بنجاح.\n"
    "الرقم السابق: {old_whatsapp_phone}\n"
    "الرقم الجديد: {new_whatsapp_phone}"
)
TRANSLATIONS["ar"]["dashboard"]["messages"]["invalid_support_username"] = (
    "أرسل يوزر تيليجرام صحيح."
)
TRANSLATIONS["ar"]["dashboard"]["messages"]["support_username_updated"] = (
    "تم تحديث يوزر الدعم بنجاح.\n"
    "القيمة السابقة: @{old_support_username}\n"
    "القيمة الجديدة: @{new_support_username}"
)
TRANSLATIONS["ar"]["wallet"]["topup_approved_to_user"] = (
    "تمت الموافقة على إيداعك في المحفظة.\n\n"
    "المبلغ المضاف: {amount} {currency}\n"
    "طريقة الدفع: {payment_method}\n"
    "رصيدك الحالي: {balance} {currency}"
)

TRANSLATIONS["ar"]["wallet"]["topup_rejected_to_user"] = (
    "تم رفض طلب إيداعك في المحفظة.\n\n"
    "المبلغ: {amount} {currency}\n"
    "طريقة الدفع: {payment_method}\n\n"
    "إذا كنت تحتاج إلى مساعدة، تواصل مع الدعم."
)

TRANSLATIONS["ar"]["dashboard"]["buttons"]["edit_credentials"] = "تعديل بيانات الحسابات"
TRANSLATIONS["ar"]["dashboard"]["buttons"]["set_special_products"] = "تحديد المنتجات المميزة"
TRANSLATIONS["ar"]["dashboard"]["add"]["ask_image"] = "أرسل صورة المنتج."
TRANSLATIONS["ar"]["dashboard"]["add"]["ask_account_type"] = "اختر نوع الحساب:"
TRANSLATIONS["ar"]["dashboard"]["validation"]["invalid_image"] = "أرسل صورة من فضلك."
TRANSLATIONS["ar"]["wallet"]["cancel_topup_button"] = "إلغاء عملية الإيداع"
TRANSLATIONS["ar"]["wallet"]["topup_cancelled"] = "تم إلغاء عملية الإيداع وتم اعتبار الطلب منتهيًا."
