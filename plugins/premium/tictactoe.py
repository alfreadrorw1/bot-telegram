# plugins/premium/tictactoe.py
import json
import os
import random
import asyncio
from telethon import events, Button
from telethon.tl.types import InputWebDocument
from telethon.tl.types import (
    InputBotInlineMessageID,
    InputBotInlineMessageText,
    InputBotInlineResult,
)
from config import OWNER_ID, BOT_USERNAME

def get_user_folder(user_id=None):
    """Get user-specific folder path"""
    if user_id is None or user_id == OWNER_ID:
        return 'premium'
    return f'premium/userprem_{user_id}'

def get_prefix(user_id=None):
    """Get current prefix for specific user"""
    user_folder = get_user_folder(user_id)
    try:
        with open(f'{user_folder}/prefix.json', 'r') as f:
            return json.load(f).get('prefix', '.')
    except (FileNotFoundError, json.JSONDecodeError):
        os.makedirs(user_folder, exist_ok=True)
        with open(f'{user_folder}/prefix.json', 'w') as f:
            json.dump({'prefix': '.'}, f)
        return '.'

def is_premium_user(user_id):
    """Check if user is premium"""
    try:
        with open('premium/premium.json', 'r') as f:
            premium_data = json.load(f)
            return str(user_id) in premium_data.get("users", [])
    except (FileNotFoundError, json.JSONDecodeError):
        return False

# Game state management
GAME_FILE = 'data/tictactoe_games.json'

def load_games():
    """Load all active games"""
    try:
        if not os.path.exists(GAME_FILE):
            os.makedirs(os.path.dirname(GAME_FILE), exist_ok=True)
            return {}
        with open(GAME_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def save_games(games):
    """Save all active games"""
    os.makedirs(os.path.dirname(GAME_FILE), exist_ok=True)
    with open(GAME_FILE, 'w') as f:
        json.dump(games, f, indent=2)

def create_game(chat_id, player1_id, player1_name):
    """Create a new game"""
    games = load_games()
    game_id = f"{chat_id}_{player1_id}"
    
    game_data = {
        "player1": {"id": player1_id, "name": player1_name, "symbol": "❌"},
        "player2": None,
        "board": [" " for _ in range(9)],
        "current_turn": player1_id,
        "status": "waiting",  # waiting, playing, finished
        "winner": None,
        "moves": 0,
        "inline_message_id": None
    }
    
    games[game_id] = game_data
    save_games(games)
    return game_id

def join_game(game_id, player2_id, player2_name):
    """Join an existing game"""
    games = load_games()
    if game_id in games and games[game_id]["player2"] is None:
        games[game_id]["player2"] = {"id": player2_id, "name": player2_name, "symbol": "⭕"}
        games[game_id]["status"] = "playing"
        games[game_id]["current_turn"] = random.choice([games[game_id]["player1"]["id"], player2_id])
        save_games(games)
        return True
    return False

def make_move(game_id, player_id, position):
    """Make a move in the game"""
    games = load_games()
    if game_id not in games:
        return False, "Game not found"
    
    game = games[game_id]
    
    # Check if it's player's turn
    if game["current_turn"] != player_id:
        return False, "Not your turn"
    
    # Check if position is valid
    if position < 0 or position >= 9 or game["board"][position] != " ":
        return False, "Invalid move"
    
    # Determine player symbol
    if player_id == game["player1"]["id"]:
        symbol = game["player1"]["symbol"]
    else:
        symbol = game["player2"]["symbol"]
    
    # Make the move
    game["board"][position] = symbol
    game["moves"] += 1
    
    # Check for winner
    winner = check_winner(game["board"])
    if winner:
        game["status"] = "finished"
        game["winner"] = player_id
    elif game["moves"] == 9:
        game["status"] = "finished"
        game["winner"] = "draw"
    else:
        # Switch turn
        if player_id == game["player1"]["id"]:
            game["current_turn"] = game["player2"]["id"]
        else:
            game["current_turn"] = game["player1"]["id"]
    
    save_games(games)
    return True, "Move successful"

def check_winner(board):
    """Check if there's a winner"""
    # Winning combinations
    win_combinations = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],  # Rows
        [0, 3, 6], [1, 4, 7], [2, 5, 8],  # Columns
        [0, 4, 8], [2, 4, 6]              # Diagonals
    ]
    
    for combo in win_combinations:
        if board[combo[0]] != " " and board[combo[0]] == board[combo[1]] == board[combo[2]]:
            return True
    return False

def get_board_buttons(board, game_id, is_player_turn):
    """Generate buttons for the game board"""
    buttons = []
    row = []
    
    for i in range(9):
        if board[i] == " ":
            # Empty cell - show number if it's player's turn
            if is_player_turn:
                button_text = f"{i+1}"
            else:
                button_text = "⬜"
            row.append(Button.inline(button_text, f"ttt_{game_id}_{i}"))
        else:
            # Occupied cell
            if board[i] == "❌":
                # Red X
                row.append(Button.inline("❌", f"ttt_none"))
            else:
                # Green O
                row.append(Button.inline("⭕", f"ttt_none"))
        
        # Create new row every 3 buttons
        if len(row) == 3:
            buttons.append(row)
            row = []
    
    return buttons

def get_game_info(game_data):
    """Get game information text"""
    if game_data["status"] == "waiting":
        return f"🎮 Game TicTacToe\n\n👤 Player 1: {game_data['player1']['name']}\n⏳ Menunggu player 2 bergabung..."
    
    player1 = game_data["player1"]
    player2 = game_data["player2"]
    
    info = f"🎮 Game TicTacToe\n\n"
    info += f"❌ {player1['name']}\n"
    info += f"⭕ {player2['name']}\n\n"
    
    if game_data["status"] == "playing":
        current_player = player1 if game_data["current_turn"] == player1["id"] else player2
        info += f"🎯 Giliran: {current_player['name']} ({current_player['symbol']})"
    else:
        if game_data["winner"] == "draw":
            info += "🤝 SERI!\nTidak ada pemenang"
        else:
            winner = player1 if game_data["winner"] == player1["id"] else player2
            info += f"🏆 Pemenang: {winner['name']} ({winner['symbol']})"
    
    return info

def create_ttt_caption(player_name):
    return (
        f"🎮 Game TicTacToe\n\n"
        f"👤 Player 1: {player_name}\n"
        f"⏳ Menunggu player 2 bergabung...\n\n"
        f"Klik tombol di bawah untuk bergabung!"
    )

async def setup(bot, client, user_id):
    """Setup TicTacToe game for premium users"""
    current_user_id = user_id

    @bot.on(events.InlineQuery)
    async def ttt_inline_handler(event):
        """Handle TicTacToe inline queries"""
        # Check authorization
        sender_id = event.sender_id
        is_authorized = (
            sender_id == OWNER_ID or 
            (is_premium_user(sender_id) and current_user_id == sender_id))
        
        if not is_authorized:
            return

        query = event.text.strip()
        
        # Check if it's a TicTacToe query
        if query and query.startswith("ttt"):
            try:
                # Create new game via inline
                sender = await event.get_sender()
                player_name = sender.first_name or "Player"
                if sender.last_name:
                    player_name += f" {sender.last_name}"
                
                game_id = create_game(f"inline_{event.id}", sender_id, player_name)
                
                # Create inline result using the same pattern as font.py
                result = event.builder.article(
                    title="🎮 TicTacToe Game",
                    description="Klik untuk memulai game TicTacToe",
                    text=create_ttt_caption(player_name),
                    buttons=[[Button.inline("🎮 Bergabung dengan Game", f"ttt_join_{game_id}")]]
                )
                
                await event.answer([result])
            except Exception as e:
                print(f"Error in TTT inline handler: {e}")

    @client.on(events.NewMessage())
    async def ttt_handler(event):
        """Handle TicTacToe commands"""
        # Check authorization
        sender_id = event.sender_id
        is_authorized = (
            sender_id == OWNER_ID or 
            (is_premium_user(sender_id) and current_user_id == sender_id))
        
        if not is_authorized:
            return

        current_prefix = get_prefix(current_user_id)
        msg = (event.text or '').strip()
        
        # TicTacToe command
        if msg.startswith(f"{current_prefix}ttt") or msg.startswith(f"{current_prefix}tictactoe"):
            # Check if in private chat
            if not event.is_private:
                status = await event.reply("<blockquote>❌ Game hanya bisa dimainkan di chat private!</blockquote>", parse_mode="html")
                await asyncio.sleep(3)
                await status.delete()
                return
            
            # Create new game
            sender = await event.get_sender()
            player_name = sender.first_name or "Player"
            if sender.last_name:
                player_name += f" {sender.last_name}"
            
            game_id = create_game(event.chat_id, sender_id, player_name)
            
            # Send join message with button
            join_button = [
                [Button.inline("🎮 Bergabung dengan Game", f"ttt_join_{game_id}")]
            ]
            
            # Format pesan dengan button di bagian bawah
            message_text = (
                f"🎮 Game TicTacToe\n\n"
                f"👤 Player 1: {player_name}\n"
                f"⏳ Menunggu player 2 bergabung...\n\n"
                f"Klik tombol di bawah untuk bergabung!"
            )
            
            await event.reply(message_text, buttons=join_button)
            await event.delete()

    @bot.on(events.CallbackQuery(pattern=r"ttt_join_(\w+)"))
    async def ttt_join_handler(event):
        """Handle join game callback"""
        try:
            game_id = event.pattern_match.group(1).decode()
            games = load_games()
            
            if game_id not in games:
                await event.answer("Game tidak ditemukan atau sudah berakhir!", alert=True)
                return
            
            game = games[game_id]
            
            # Check if game is already full
            if game["player2"] is not None:
                await event.answer("Game sudah penuh!", alert=True)
                return
            
            # Check if player is trying to join their own game
            if event.sender_id == game["player1"]["id"]:
                await event.answer("Anda tidak bisa bergabung dengan game sendiri!", alert=True)
                return
            
            # Join the game
            sender = await event.get_sender()
            player_name = sender.first_name or "Player"
            if sender.last_name:
                player_name += f" {sender.last_name}"
            
            success = join_game(game_id, event.sender_id, player_name)
            
            if success:
                # Update message with game board
                game = games[game_id]
                is_player_turn = game["current_turn"] == event.sender_id
                
                buttons = get_board_buttons(game["board"], game_id, is_player_turn)
                game_info = get_game_info(game)
                
                await event.edit(
                    game_info,
                    buttons=buttons
                )
                await event.answer("Berhasil bergabung dengan game!")
            else:
                await event.answer("Gagal bergabung dengan game!", alert=True)
                
        except Exception as e:
            await event.answer("Error saat bergabung dengan game!", alert=True)
            print(f"TTT join error: {e}")

    @bot.on(events.CallbackQuery(pattern=r"ttt_(\w+)_(\d)"))
    async def ttt_move_handler(event):
        """Handle game move callback"""
        try:
            game_id = event.pattern_match.group(1).decode()
            position = int(event.pattern_match.group(2).decode())
            games = load_games()
            
            if game_id not in games:
                await event.answer("Game tidak ditemukan!", alert=True)
                return
            
            game = games[game_id]
            
            # Check if game is still active
            if game["status"] != "playing":
                await event.answer("Game sudah selesai!", alert=True)
                return
            
            # Check if user is part of this game
            if event.sender_id not in [game["player1"]["id"], game["player2"]["id"]]:
                await event.answer("Anda bukan peserta game ini!", alert=True)
                return
            
            # Make the move
            success, message = make_move(game_id, event.sender_id, position)
            
            if not success:
                await event.answer(message, alert=True)
                return
            
            # Update the game board
            games = load_games()
            game = games[game_id]
            
            # Check if game is finished
            if game["status"] == "finished":
                buttons = get_board_buttons(game["board"], game_id, False)
                game_info = get_game_info(game)
                
                # Add play again button
                buttons.append([Button.inline("🔄 Main Lagi", f"ttt_new_{event.chat_id}")])
                
                await event.edit(
                    game_info,
                    buttons=buttons
                )
                await event.answer("Move berhasil! Game selesai.")
            else:
                # Game continues
                is_player_turn = game["current_turn"] == event.sender_id
                buttons = get_board_buttons(game["board"], game_id, is_player_turn)
                game_info = get_game_info(game)
                
                await event.edit(
                    game_info,
                    buttons=buttons
                )
                await event.answer("Move berhasil!")
                
        except Exception as e:
            await event.answer("Error saat melakukan move!", alert=True)
            print(f"TTT move error: {e}")

    @bot.on(events.CallbackQuery(pattern=r"ttt_new_(\w+)"))
    async def ttt_new_handler(event):
        """Handle new game callback"""
        try:
            chat_id = int(event.pattern_match.group(1).decode())
            
            # Create new game
            sender = await event.get_sender()
            player_name = sender.first_name or "Player"
            if sender.last_name:
                player_name += f" {sender.last_name}"
            
            game_id = create_game(chat_id, event.sender_id, player_name)
            
            # Send join message with button
            join_button = [
                [Button.inline("🎮 Bergabung dengan Game", f"ttt_join_{game_id}")]
            ]
            
            # Format pesan dengan button di bagian bawah
            message_text = (
                f"🎮 Game TicTacToe\n\n"
                f"👤 Player 1: {player_name}\n"
                f"⏳ Menunggu player 2 bergabung...\n\n"
                f"Klik tombol di bawah untuk bergabung!"
            )
            
            await event.edit(
                message_text,
                buttons=join_button
            )
            
            await event.answer("Game baru dibuat!")
                
        except Exception as e:
            await event.answer("Error membuat game baru!", alert=True)
            print(f"TTT new game error: {e}")

    @bot.on(events.CallbackQuery(pattern=r"ttt_none"))
    async def ttt_none_handler(event):
        """Handle invalid button clicks"""
        await event.answer("Posisi ini sudah terisi!", alert=True)

    # Userbot handler: trigger inline
    @client.on(events.NewMessage(outgoing=True))
    async def ttt_command_handler(event):
        """Handle ttt command to trigger inline query"""
        sender_id = event.sender_id
        is_authorized = (
            sender_id == OWNER_ID or 
            (is_premium_user(sender_id) and current_user_id == sender_id))
        
        if not is_authorized:
            return

        msg = (event.text or '').strip()
        current_prefix = get_prefix(current_user_id)
        
        is_ttt_cmd = False
        
        if current_prefix == "no":
            if msg.lower().startswith("ttt"):
                is_ttt_cmd = True
        else:
            if msg.startswith(current_prefix):
                cmd = msg[len(current_prefix):].strip().lower()
                if cmd.startswith("ttt"):
                    is_ttt_cmd = True

        if not is_ttt_cmd:
            return

        try:
            await event.delete()
            result = await client.inline_query(BOT_USERNAME, "ttt")
            if result:
                await result[0].click(event.chat_id)
        except Exception as e:
            print(f"Error in ttt_command_handler: {e}")
            await event.respond("⚠️ Gagal memunculkan game TicTacToe")