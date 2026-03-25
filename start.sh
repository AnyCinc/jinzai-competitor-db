#!/bin/bash
# ═══════════════════════════════════════════════════
# 競合調査DB - ローカル起動 + Cloudflare Tunnel 公開
# ═══════════════════════════════════════════════════
# 使い方: ターミナルで ./start.sh を実行するだけ
# 終了: Ctrl+C

cd "$(dirname "$0")"

echo ""
echo "=================================="
echo "  競合調査DB を起動します..."
echo "=================================="
echo ""

# Streamlitをバックグラウンドで起動
streamlit run streamlit_app.py --server.port 8501 --server.headless true &
STREAMLIT_PID=$!

# Streamlitの起動を待つ
echo "⏳ Streamlit 起動中..."
sleep 3

# Cloudflare Tunnelで公開
echo ""
echo "🌐 Cloudflare Tunnel で公開中..."
echo "   （下にURLが表示されます）"
echo ""

~/.local/bin/cloudflared tunnel --url http://localhost:8501 2>&1 | while read line; do
    # trycloudflare.com のURLを見つけたら表示
    if echo "$line" | grep -q "trycloudflare.com"; then
        URL=$(echo "$line" | grep -o 'https://[^ ]*trycloudflare.com[^ ]*')
        if [ -n "$URL" ]; then
            echo ""
            echo "=================================="
            echo "  ✅ 公開URL:"
            echo "  $URL"
            echo "=================================="
            echo ""
            echo "  このURLを共有すれば誰でもアクセスできます"
            echo "  終了するには Ctrl+C を押してください"
            echo ""
        fi
    fi
done

# 終了時にStreamlitも停止
kill $STREAMLIT_PID 2>/dev/null
echo "停止しました。"
