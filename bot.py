# 在 on_modal_submit 事件中

# --- Tokens login ---
elif interaction.data.get("title") == "Paste Tokens":
    app_rt = interaction.data["components"][0]["components"][0]["value"]
    app_at = interaction.data["components"][1]["components"][0]["value"]
    try:
        # 使用新的认证类进行验证
        test_auth = BloxflipAuth(app_rt=app_rt, app_at=app_at)
        test_session = test_auth.get_session()
        # 发送一个测试请求
        resp = test_session.get("https://bloxflip.com/api/user/profile")
        if resp.status_code != 200:
            await interaction.response.send_message("❌ Invalid tokens – could not fetch profile. Check your app.rt and app.at values.", ephemeral=True)
            return
        # 验证通过，存储会话
        predictor.set_user_session(interaction.user.id, {"type": "tokens", "app_rt": app_rt, "app_at": app_at})
        await interaction.response.send_message("✅ Successfully connected with tokens!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Authentication failed: {str(e)}", ephemeral=True)
