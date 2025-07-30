from rag_tinyllama_new import TextbookRAG
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import threading
import time
from datetime import datetime
import re
import difflib

class SocialcienceChatbot:
    def __init__(self, root):
        self.root = root
        self.root.title("SOCIAL SCIENCE CHATBOT")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f8fafc')
        
        # Data variables
        
        self.all_sessions = {}
        self.current_session_id = None
        self.is_loading = False
        
        # Load freedom fighter data
        #self.load_freedom_fighter_data()
        
        # Create GUI
        self.create_widgets()
        
        # Start with a new chat
        self.start_new_chat()
        
        # Focus on input
        self.root.after(100, lambda: self.message_entry.focus())

        # Load the TinyLLaMA QA model
        self.qa_bot = TextbookRAG(
            index_file="faiss_index.index",
            chunks_file="faiss_index_chunks_with_improved_tags.json",
            llama_model_path="C:/Users/Siansha Bhushan/Desktop/class8_2/models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
            ) # full path if needed)

    def style_button(self, button, bg_color="#6366f1", fg_color="white", font=('Segoe UI', 11, 'bold')):
        button.config(
            bg=bg_color,
            fg=fg_color,
            font=font,
            relief=tk.FLAT,
            bd=0,
            padx=20,
            pady=10,
            cursor="hand2",
            activebackground=bg_color,
            activeforeground=fg_color
        )
    
    # def load_freedom_fighter_data(self):
    #     """Load freedom fighter data from JSON file"""
    #     try:
    #         with open('freedom_fighters.json', 'r', encoding='utf-8') as file:
    #             data = json.load(file)
    #             self.freedom_fighters = data
    #             print(f"Loaded {len(self.freedom_fighters)} freedom fighters")
    #     except FileNotFoundError:
    #         messagebox.showerror("Error", "freedom_fighter.json file not found!")
    #         self.freedom_fighters = {}
    #     except json.JSONDecodeError:
    #         messagebox.showerror("Error", "Invalid JSON format in freedom_fighter.json!")
    #         self.freedom_fighters = {}
    
    def create_widgets(self):
        """Create all GUI widgets"""
        # Main container
        main_frame = tk.Frame(self.root, bg='#f8fafc')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create sidebar and main chat area
        self.create_sidebar(main_frame)
        self.create_chat_area(main_frame)
        
        # Create info panel (initially hidden)
        self.create_info_panel()
    
    def create_sidebar(self, parent):
        """Create sidebar with session management"""
        # Sidebar frame
        sidebar_frame = tk.Frame(parent, bg='#6366f1', width=280)
        sidebar_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 2))
        sidebar_frame.pack_propagate(False)
        
        # Sidebar header
        header_frame = tk.Frame(sidebar_frame, bg='#5856eb', height=100)
        header_frame.pack(fill=tk.X, pady=(0, 1))
        header_frame.pack_propagate(False)
        
        # Title
        title_label = tk.Label(header_frame, text="SOCIAL SCIENCE", 
                              font=('Segoe UI', 16, 'bold'), fg='white', bg='#5856eb')
        title_label.pack(pady=(15, 10))
        
        # New chat button
        self.new_chat_btn = tk.Button(header_frame, text="✨ New Chat", 
                                     font=('Segoe UI', 10), bg='#7c3aed', fg='white',
                                     relief=tk.FLAT, cursor='hand2', pady=8,
                                     command=self.start_new_chat)
        self.style_button(self.new_chat_btn)
        self.new_chat_btn.pack(pady=(0, 15), padx=20, fill=tk.X)
        
        # Sessions list
        sessions_frame = tk.Frame(sidebar_frame, bg='#6366f1')
        sessions_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Sessions scrollable area
        self.sessions_canvas = tk.Canvas(sessions_frame, bg='#6366f1', highlightthickness=0)
        sessions_scrollbar = ttk.Scrollbar(sessions_frame, orient="vertical", command=self.sessions_canvas.yview)
        self.sessions_scrollable_frame = tk.Frame(self.sessions_canvas, bg='#6366f1')
        
        self.sessions_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.sessions_canvas.configure(scrollregion=self.sessions_canvas.bbox("all"))
        )
        
        self.sessions_canvas.create_window((0, 0), window=self.sessions_scrollable_frame, anchor="nw")
        self.sessions_canvas.configure(yscrollcommand=sessions_scrollbar.set)
        
        self.sessions_canvas.pack(side="left", fill="both", expand=True)
        sessions_scrollbar.pack(side="right", fill="y")
    
    def create_chat_area(self, parent):
        """Create main chat area"""
        # Chat container
        chat_frame = tk.Frame(parent, bg='#f8fafc')
        chat_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Chat header
        header_frame = tk.Frame(chat_frame, bg='#6366f1', height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        # Header content
        header_content = tk.Frame(header_frame, bg='#6366f1')
        header_content.pack(expand=True, fill=tk.BOTH)
        
        # Close (X) button
        close_button = tk.Button(header_frame, text="❌", font=('Segoe UI', 10, 'bold'),
                         bg='#6366f1', fg='white', relief=tk.FLAT, borderwidth=0,
                         command=self.root.destroy)
        self.style_button(close_button)
        close_button.place(relx=1.0, x=-10, y=10, anchor="ne")

        # Title
        title_label = tk.Label(header_content, text="SOCIAL SCIENCE", 
                              font=('Segoe UI', 18, 'bold'), fg='white', bg='#6366f1')
        title_label.pack(pady=(15, 5))
        
        subtitle_label = tk.Label(header_content, text="Learn about Social Science with AI-powered knowledge", 
                                 font=('Segoe UI', 10), fg='#e0e7ff', bg='#6366f1')
        subtitle_label.pack()
        
        # Control buttons
        controls_frame = tk.Frame(header_content, bg='#6366f1')
        controls_frame.pack(side=tk.RIGHT, anchor='ne', padx=20, pady=10)
        
        help_btn = tk.Button(controls_frame, text="ℹ️ Help", font=('Segoe UI', 9),
                            bg='#7c3aed', fg='white', relief=tk.FLAT, cursor='hand2',
                            command=self.show_info)
        self.style_button(help_btn)
        help_btn.pack(side=tk.RIGHT, padx=5)
        
        clear_btn = tk.Button(controls_frame, text="🗑️ Clear", font=('Segoe UI', 9),
                             bg='#7c3aed', fg='white', relief=tk.FLAT, cursor='hand2',
                             command=self.clear_current_chat)
        self.style_button(clear_btn)
        clear_btn.pack(side=tk.RIGHT, padx=5)
        
        # Chat messages area
        self.create_chat_messages_area(chat_frame)
        
        # Input area
        self.create_input_area(chat_frame)


    def create_chat_messages_area(self, parent):
        messages_frame = tk.Frame(parent, bg='#f8fafc')
        messages_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        self.messages_text = scrolledtext.ScrolledText(
            messages_frame, 
            wrap=tk.WORD,
            font=('Segoe UI', 11),
            bg='#f8fafc',
            fg='#374151',
            relief=tk.FLAT,
            borderwidth=0,
            state=tk.NORMAL,  # Keep NORMAL to allow selection
            insertbackground='#000000',
            selectbackground="#8a8efd",   # Blue highlight
                
        )
        self.messages_text.pack(fill=tk.BOTH, expand=True)

        # Prevent editing but allow text selection and Ctrl+C
        def block_typing(event):
            if event.state & 0x4 and event.keysym.lower() in ['c', 'a']:  # Ctrl+C or Ctrl+A
                return
            return "break"  # Block everything else

        # Allow mouse-based text selection
        self.messages_text.bind("<Key>", block_typing)

        self.messages_text.tag_config('user_message', background='#6366f1', foreground='white',
                                  font=('Segoe UI', 11), rmargin=80, justify='left',
                                  relief=tk.FLAT, borderwidth=10)
        self.messages_text.tag_config('bot_message',
                        foreground='#374151',
                        font=('Segoe UI', 11),
                        lmargin1=20,
                        lmargin2=20
                    )
        
        self.messages_text.tag_config('time_info', font=('Segoe UI', 9), foreground='#9ca3af')
        self.messages_text.tag_config('welcome_title', font=('Segoe UI', 16, 'bold'), 
                                    foreground='#2c3e50', justify='center')
        self.messages_text.tag_config('welcome_text', font=('Segoe UI', 11), 
                                    foreground='#6b7280', justify='center')
        self.messages_text.tag_config('example_text', font=('Segoe UI', 10), 
                                    foreground='#6366f1', underline=True)

        # Context menu
        self.create_context_menu()

    
    # def create_chat_messages_area(self, parent):
    #     """Create chat messages display area"""
    #     # Messages frame
    #     messages_frame = tk.Frame(parent, bg='#f8fafc')
    #     messages_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    #     # Scrollable text area
    #     self.messages_text = scrolledtext.ScrolledText(
    #     messages_frame, 
    #     wrap=tk.WORD,
    #     font=('Segoe UI', 11),
    #     bg='#f8fafc',
    #     fg='#374151',
    #     relief=tk.FLAT,
    #     borderwidth=0,
    #     state=tk.NORMAL,  # Start with NORMAL state
    #     insertbackground='#000000',  
    #     selectbackground='#3b82f6',  # Fixed: Better selection color
    #     selectforeground='Red'
    # )
    #     self.messages_text.pack(fill=tk.BOTH, expand=True)

    #     # FIXED: Proper text selection handling
    #     def on_key_press(event):
    #         # Allow selection keys and copy operations
    #         allowed_keys = [
    #         'Left', 'Right', 'Up', 'Down', 'Home', 'End', 
    #         'Prior', 'Next', 'Shift_L', 'Shift_R'
    #         ]
        
    #         # Allow Ctrl+C and Ctrl+A
    #         if event.state & 0x4:  # Ctrl is pressed
    #             if event.keysym.lower() in ['c', 'a']:
    #                 return
        
    #         # Allow selection keys
    #         if event.keysym in allowed_keys:
    #             return
            
    #         # Block all other keys
    #         return "break"

    #     # FIXED: Proper mouse event handling
    #     def on_button_press(event):
    #         # Allow selection but prevent cursor positioning for editing
    #         self.messages_text.focus_set()
    #         return

    #     def on_button_motion(event):
    #         # Allow selection dragging
    #         return

    #     def on_button_release(event):
    #         # Allow selection completion
    #         return

    #     # Bind events properly
    #     self.messages_text.bind("<KeyPress>", on_key_press)
    #     # self.messages_text.bind("<Button-1>", on_button_press)
    #     # self.messages_text.bind("<B1-Motion>", on_button_motion)
    #     # self.messages_text.bind("<ButtonRelease-1>", on_button_release)

    #     # Configure text tags for styling
    #     self.messages_text.tag_config('user_message', background='#6366f1', foreground='white',
    #                          font=('Segoe UI', 11), rmargin=80, justify='left',
    #                          relief=tk.FLAT, borderwidth=10)
    #     self.messages_text.tag_config('bot_message', background='white', foreground='#374151',
    #                          font=('Segoe UI', 11), lmargin1=20, lmargin2=20,
    #                          relief=tk.FLAT, borderwidth=10)
    #     self.messages_text.tag_config('time_info', font=('Segoe UI', 9), foreground='#9ca3af')
    #     self.messages_text.tag_config('welcome_title', font=('Segoe UI', 16, 'bold'), 
    #                          foreground='#2c3e50', justify='center')
    #     self.messages_text.tag_config('welcome_text', font=('Segoe UI', 11), 
    #                          foreground='#6b7280', justify='center')
    #     self.messages_text.tag_config('example_text', font=('Segoe UI', 10), 
    #                          foreground='#6366f1', underline=True)

    #     # Add context menu for copy functionality
    #     self.create_context_menu()
    
    def create_context_menu(self):
        """Create context menu for copy functionality"""
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Copy", command=self.copy_selected_text)
        self.context_menu.add_command(label="Select All", command=self.select_all_text)
        self.context_menu.add_command(label="Clear Selection", command=self.clear_selection)

        # Bind events for text selection and context menu
        self.messages_text.bind("<Button-3>", self.show_context_menu)
        self.messages_text.bind("<Control-c>", lambda e: self.copy_selected_text())
        self.messages_text.bind("<Control-a>", lambda e: self.select_all_text())

    def enable_text_selection(self, event=None):
        """Enable text selection temporarily"""
        self.messages_text.config(state=tk.NORMAL)
        return "break"  # Prevent default behavior

    def disable_text_selection(self, event=None):
        """Disable text editing but keep selection visible"""
        # Don't disable immediately - let the selection happen first
        self.root.after(10, lambda: self.messages_text.config(state=tk.NORMAL))

    def show_context_menu(self, event):
        """Show context menu on right-click"""
        try:
            # Update context menu based on selection
            has_selection = bool(self.messages_text.tag_ranges(tk.SEL))
        
            # Enable/disable menu items based on selection
            self.context_menu.entryconfig("Copy", state=tk.NORMAL if has_selection else tk.NORMAL)
        
            # Show context menu
            self.context_menu.tk_popup(event.x_root, event.y_root)
        
        except Exception as e:
            print(f"Error showing context menu: {e}")

    def copy_selected_text(self):
        """Copy selected text to clipboard"""
        try:
            # Check if there's selected text
            if self.messages_text.tag_ranges(tk.SEL):
                selected_text = self.messages_text.get(tk.SEL_FIRST, tk.SEL_LAST)
            
                
                # Copy to clipboard
                self.root.clipboard_clear()
                self.root.clipboard_append(selected_text)
            
                # Show confirmation
                self.show_temporary_message("Text copied to clipboard!")
            else:
                self.show_temporary_message("No text selected!")
        
        except Exception as e:
            self.show_temporary_message("Error copying text!")
            print(f"Copy error: {e}")

    def select_all_text(self):
        """Select all text in chat area"""
        try:
            self.messages_text.tag_add(tk.SEL, "1.0", tk.END)
            self.messages_text.mark_set(tk.INSERT, "1.0")
            self.messages_text.see(tk.INSERT)
            return "break"  # Prevent default behavior
        except Exception as e:
            print(f"Error selecting all text: {e}")
            return "break"

    def clear_selection(self):
        """Clear text selection"""
        try:
            self.messages_text.tag_remove(tk.SEL, "1.0", tk.END)
        except Exception as e:
            print(f"Error clearing selection: {e}")
    
    def show_temporary_message(self, message):
        """Show a temporary message in the status area"""
        # Create a temporary label that disappears after 2 seconds
        temp_label = tk.Label(self.root, text=message, bg='#10b981', fg='white', 
                             font=('Segoe UI', 10), padx=10, pady=5)
        temp_label.place(relx=0.5, rely=0.95, anchor='center')
        
        # Remove the label after 2 seconds
        self.root.after(2000, temp_label.destroy)
    
    def create_input_area(self, parent):
        """Create message input area"""
        #input_frame = tk.Frame(parent, bg='white', height=150)
        input_frame = tk.Frame(parent, bg='white')
        #input_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        input_frame.pack(fill=tk.BOTH, expand=True)

        #input_frame.pack_propagate(False)
        
        # Input wrapper
        input_wrapper = tk.Frame(input_frame, bg='white')
        input_wrapper.pack(expand=True, fill=tk.BOTH, padx=20, pady=15)
        
        # Message entry and send button row
        input_row = tk.Frame(input_wrapper, bg='white')
        input_row.pack(fill=tk.BOTH,expand=True,pady=(0, 10))
        
        # Use Text widget instead of Entry for better handling of long text
        self.message_entry = tk.Text(
            input_row,
            font=('Segoe UI', 12),
            bg='#f9fafb',
            fg='#9ca3af',
            relief=tk.FLAT,
            borderwidth=2,
            height=3,  # 3 lines height
            wrap=tk.WORD
        )
        
        # Placeholder text
        self.placeholder_text = "Type your question here..."
        self.is_placeholder_active = True
        
        self.message_entry.insert('1.0', self.placeholder_text)
        self.message_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Placeholder handling functions
        def on_entry_click(event):
            """Handle when user clicks on the entry field"""
            if self.is_placeholder_active:
                self.message_entry.delete('1.0', tk.END)
                self.message_entry.config(fg='#1f2937')
                self.is_placeholder_active = False
        
        def on_focus_out(event):
            """Handle when user clicks away from the entry field"""
            current_text = self.message_entry.get('1.0', tk.END).strip()
            if current_text == "" or current_text == self.placeholder_text:
                self.message_entry.delete('1.0', tk.END)
                self.message_entry.insert('1.0', self.placeholder_text)
                self.message_entry.config(fg='#9ca3af')
                self.is_placeholder_active = True
        
        def on_key_press(event):
            """Handle key press events"""
            # If placeholder is active and user types, clear it
            if self.is_placeholder_active and event.keysym not in ['Tab', 'Shift_L', 'Shift_R', 'Control_L', 'Control_R', 'Alt_L', 'Alt_R']:
                self.message_entry.delete('1.0', tk.END)
                self.message_entry.config(fg='#1f2937')
                self.is_placeholder_active = False
            
            # Handle Enter key (Shift+Enter for new line, Enter to send)
            if event.keysym == 'Return':
                if event.state & 0x1:  # Shift+Enter
                    return  # Allow new line
                else:  # Enter only
                    self.send_message()
                    return 'break'  # Prevent default Enter behavior
        
        # Bind events
        self.message_entry.bind('<FocusIn>', on_entry_click)
        self.message_entry.bind('<FocusOut>', on_focus_out)
        self.message_entry.bind('<KeyPress>', on_key_press)
        
        # Send button
        self.send_btn = tk.Button(
            input_row,
            text="Send",
            font=('Segoe UI', 12, 'bold'),
            bg='#6366f1',
            fg='white',
            relief=tk.FLAT,
            cursor='hand2',
            padx=25,
            command=self.send_message
        )
        self.style_button(self.send_btn)
        self.send_btn.pack(side=tk.RIGHT)
        
        # Clear button row
        clear_row = tk.Frame(input_wrapper, bg='white')
        clear_row.pack(fill=tk.X,expand=True)
        
        # Clear button (equivalent to new chat)
        self.clear_input_btn = tk.Button(
            clear_row,
            text="🆕 Clear & Start Fresh",
            font=('Segoe UI', 10),
            bg='#10b981',
            fg='white',
            relief=tk.FLAT,
            cursor='hand2',
            padx=20,
            command=self.start_new_chat
        )
        self.style_button(self.clear_input_btn)
        self.clear_input_btn.pack(expand=True)

    
    def create_info_panel(self):
        """Create info panel (hidden by default)"""
        self.info_window = None
    
    def show_info(self):
        """Show info panel in a new window"""
        if self.info_window and self.info_window.winfo_exists():
            self.info_window.lift()
            return
        
        self.info_window = tk.Toplevel(self.root)
        self.info_window.title("How to Use - Social Science Chatbot")
        self.info_window.geometry("400x600")
        self.info_window.configure(bg='white')
        
        # Header
        header_frame = tk.Frame(self.info_window, bg='#6366f1', height=60)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(header_frame, text="How to Use Social Science Chatbot", 
                              font=('Segoe UI', 14, 'bold'), fg='white', bg='#6366f1')
        title_label.pack(pady=15)
        
        # Content
        content_frame = tk.Frame(self.info_window, bg='white')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Info items
        info_items = [
            ("📚 General Questions", "Ask: \"What is photosynthesis?\" or \"Explain gravity\""),
            ("🎯 Specific Class/Chapter", "Ask: \"In Class 10 Chapter 6, explain respiration\" or \"Chapter 5 class 9 light\""),
            ("🔍 Search Features", "• Semantic search across all textbook content\n• Automatic class/chapter detection\n• Context-aware answers from textbook"),
            ("💡 Tips for Better Results", "• Be specific with your questions\n• Mention class and chapter when possible\n• Use keywords from textbook content\n• Ask follow-up questions for clarification"),
            ("🖱️ Interface Features", "• Multiple chat sessions with history\n• Copy and paste functionality\n• Session management in sidebar\n• Source information for answers"),
            ("🔧 Technical Features", "• RAG (Retrieval-Augmented Generation)\n• FAISS vector search\n• LLaMA language model\n• Sentence transformers for embeddings")
        ]
        
        for title, description in info_items:
            item_frame = tk.Frame(content_frame, bg='#f8fafc', relief=tk.FLAT, borderwidth=1)
            item_frame.pack(fill=tk.X, pady=10)
            
            title_label = tk.Label(item_frame, text=title, font=('Segoe UI', 11, 'bold'), 
                                  fg='#374151', bg='#f8fafc')
            title_label.pack(anchor=tk.W, padx=15, pady=(10, 5))
            
            desc_label = tk.Label(item_frame, text=description, font=('Segoe UI', 10), 
                                 fg='#6b7280', bg='#f8fafc', wraplength=350, justify=tk.LEFT)
            desc_label.pack(anchor=tk.W, padx=15, pady=(0, 10))
        
        # Close button
        close_btn = tk.Button(content_frame, text="Close", font=('Segoe UI', 10, 'bold'),
                             bg='#6366f1', fg='white', relief=tk.FLAT, cursor='hand2',
                             command=self.info_window.destroy)
        self.style_button(close_btn)
        close_btn.pack(pady=20)
    
    def generate_session_id(self):
        """Generate unique session ID"""
        return f"session_{int(time.time())}_{id(self)}"
    
    def start_new_chat(self):
        """Start a new chat session"""
        session_id = self.generate_session_id()
        self.all_sessions[session_id] = []
        self.current_session_id = session_id
        
        self.clear_chat_messages()
        self.show_welcome_message()
        self.update_sessions_list()
        
        # Clear input field and reset placeholder
        self.message_entry.delete('1.0', tk.END)
        self.message_entry.insert('1.0', self.placeholder_text)
        self.message_entry.config(fg='#9ca3af')
        self.is_placeholder_active = True
        self.message_entry.focus()
    
    def delete_session(self, session_id):
        """Delete a specific session"""
        if len(self.all_sessions) <= 1:
            messagebox.showwarning("Cannot Delete", "You must have at least one chat session.")
            return
        
        if messagebox.askyesno("Delete Session", "Are you sure you want to delete this chat session?"):
            # Remove session from data
            if session_id in self.all_sessions:
                del self.all_sessions[session_id]
            
            # If deleted session was current, switch to another session
            if session_id == self.current_session_id:
                if self.all_sessions:
                    # Switch to the most recent session
                    self.current_session_id = max(self.all_sessions.keys(), 
                                                key=lambda x: int(x.split('_')[1]))
                    self.load_session_messages()
                else:
                    # Create new session if no sessions left
                    self.start_new_chat()
            
            # Update sessions list
            self.update_sessions_list()
    
    def clear_chat_messages(self):
        """Clear all messages from chat area"""
        # No need to change state - keep it NORMAL
        self.messages_text.delete(1.0, tk.END)
    
    def show_welcome_message(self):
        pass
    
    
    def update_sessions_list(self):
        """Update the sessions list in sidebar"""
        # Clear existing sessions
        for widget in self.sessions_scrollable_frame.winfo_children():
            widget.destroy()
        
        # Sort sessions by creation time (newest first)
        sorted_sessions = sorted(self.all_sessions.keys(), 
                               key=lambda x: int(x.split('_')[1]), reverse=True)
        
        for session_id in sorted_sessions:
            session = self.all_sessions[session_id]
            
            # Main session container
            session_container = tk.Frame(self.sessions_scrollable_frame, bg='#6366f1')
            session_container.pack(fill=tk.X, pady=5, padx=10)
            
            # Session content frame (clickable area)
            session_frame = tk.Frame(session_container, bg='#7c3aed', 
                                   relief=tk.FLAT, borderwidth=1, cursor='hand2')
            session_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
            
            # Highlight current session
            if session_id == self.current_session_id:
                session_frame.configure(bg='#8b5cf6')
            
            # Session name and preview
            session_name = "New Chat"
            session_preview = "Start chatting..."
            
            if session:
                first_user_msg = next((msg for msg in session if msg['isUser']), None)
                if first_user_msg:
                    content = first_user_msg['content']
                    session_name = content[:25] + "..." if len(content) > 25 else content
                    session_preview = f"{len(session)} message{'s' if len(session) > 1 else ''}"
            
            # Session name label
            name_label = tk.Label(session_frame, text=session_name, 
                                font=('Segoe UI', 10, 'bold'), fg='white', 
                                bg=session_frame['bg'], cursor='hand2')
            name_label.pack(anchor=tk.W, padx=15, pady=(10, 2))
            
            # Session preview label
            preview_label = tk.Label(session_frame, text=session_preview, 
                                   font=('Segoe UI', 9), fg='#e0e7ff', 
                                   bg=session_frame['bg'], cursor='hand2')
            preview_label.pack(anchor=tk.W, padx=15, pady=(0, 10))
            
            # Delete button
            delete_btn = tk.Button(session_container, text="⋮", 
                                 font=('Segoe UI', 12), bg='#7c3aed', fg='white',
                                 relief=tk.FLAT, cursor='hand2', width=3,
                                 command=lambda sid=session_id: self.delete_session(sid))
            self.style_button(delete_btn)
            delete_btn.pack(side=tk.RIGHT, padx=(0, 5))
            
            # Bind click events for session switching
            session_frame.bind("<Button-1>", lambda e, sid=session_id: self.switch_to_session(sid))
            name_label.bind("<Button-1>", lambda e, sid=session_id: self.switch_to_session(sid))
            preview_label.bind("<Button-1>", lambda e, sid=session_id: self.switch_to_session(sid))
        
        # Update scroll region
        self.sessions_canvas.configure(scrollregion=self.sessions_canvas.bbox("all"))
    
    def switch_to_session(self, session_id):
        """Switch to a different session"""
        if self.current_session_id == session_id:
            return
        
        self.current_session_id = session_id
        self.load_session_messages()
        self.update_sessions_list()
    
    def load_session_messages(self):
        """Load messages for current session"""
        self.clear_chat_messages()
        
        session = self.all_sessions[self.current_session_id]
        
        if not session:
            self.show_welcome_message()
            return
        
        self.messages_text.config(state=tk.NORMAL)
        
        for message in session:
            self.add_message_to_chat(message['content'], message['isUser'], 
                                   message['info'], scroll_to_bottom=False)
        
        self.messages_text.config(state=tk.DISABLED)
        self.messages_text.see(tk.END)
    
    def send_message(self):
        """Send message and get response"""
        if self.is_loading:
            return
        
        # Get message text, ignoring placeholder
        message = self.message_entry.get('1.0', tk.END).strip()
        if not message or message == self.placeholder_text or self.is_placeholder_active:
            return
        
        # Clear input and reset placeholder
        self.message_entry.delete('1.0', tk.END)
        self.message_entry.insert('1.0', self.placeholder_text)
        self.message_entry.config(fg='#9ca3af')
        self.is_placeholder_active = True
        
        # Add user message
        current_time = self.format_time(datetime.now())
        user_message = {
            'content': message,
            'isUser': True,
            'info': current_time
        }
        
        self.add_message_to_chat(message, True, current_time)
        self.all_sessions[self.current_session_id].append(user_message)
        
        # Show typing indicator and get response
        self.show_typing_indicator()
        
        # Process in background thread
        threading.Thread(target=self.process_message, args=(message,), daemon=True).start()
    
    def process_message(self, message):
        """Process message and get response"""
        # Simulate processing time
        time.sleep(1)
        
        # Get response
        response = self.get_chatbot_response(message)
        
        # Update UI in main thread
        self.root.after(0, self.handle_response, response)
    
    def get_chatbot_response(self, message):
        """Get response from chatbot logic"""
        result = self.qa_bot.query(question=message)
        return result["answer"]
    
    # def find_freedom_fighter(self, message):
    #     """Find freedom fighter based on message"""
    #     # Check all names and aliases
    #     for fighter_id, fighter_data in self.freedom_fighters.items():
    #         # Check main name
    #         if fighter_data.get('name', '').lower() in message:
    #             return fighter_data
            
    #         # Check aliases/nicknames
    #         aliases = fighter_data.get('aliases', [])
    #         for alias in aliases:
    #             if alias.lower() in message:
    #                 return fighter_data
        
    #     # Fuzzy matching for typos
    #     all_names = []
    #     for fighter_data in self.freedom_fighters.values():
    #         all_names.append(fighter_data.get('name', ''))
    #         all_names.extend(fighter_data.get('aliases', []))
        
    #     # Find best match
    #     best_match = difflib.get_close_matches(message, all_names, n=1, cutoff=0.6)
    #     if best_match:
    #         for fighter_data in self.freedom_fighters.values():
    #             if (fighter_data.get('name', '').lower() == best_match[0].lower() or 
    #                 best_match[0].lower() in [alias.lower() for alias in fighter_data.get('aliases', [])]):
    #                 return fighter_data
        
    #     return None
    
    # def generate_response(self, fighter, message):
    #     """Generate response based on fighter data and question type"""
    #     name = fighter.get('name', 'Unknown')
        
    #     # Birth date questions
    #     if any(word in message for word in ['born', 'birth', 'birthday']):
    #         birth_date = fighter.get('birth_date', 'Unknown')
    #         birth_place = fighter.get('birth_place', 'Unknown')
            
    #         if birth_date != 'Unknown' and birth_place != 'Unknown':
    #             return f"{name} was born on {birth_date} in {birth_place}."
    #         elif birth_date != 'Unknown':
    #             return f"{name} was born on {birth_date}."
    #         elif birth_place != 'Unknown':
    #             return f"{name} was born in {birth_place}."
    #         else:
    #             return f"I don't have specific birth information for {name}."
        
    #     # Death date questions
    #     elif any(word in message for word in ['died', 'death', 'died']):
    #         death_date = fighter.get('death_date', 'Unknown')
    #         death_place = fighter.get('death_place', 'Unknown')
            
    #         if death_date != 'Unknown' and death_place != 'Unknown':
    #             return f"{name} died on {death_date} in {death_place}."
    #         elif death_date != 'Unknown':
    #             return f"{name} died on {death_date}."
    #         elif death_place != 'Unknown':
    #             return f"{name} died in {death_place}."
    #         else:
    #             return f"I don't have specific death information for {name}."
        
    #     # Contribution questions
    #     elif any(word in message for word in ['contribute', 'contribution', 'did', 'achievement']):
    #         contributions = fighter.get('contributions', [])
    #         if contributions:
    #             return f"{name}'s main contributions include: {', '.join(contributions[:3])}."
    #         else:
    #             return f"I don't have specific contribution information for {name}."
        
    #     # General information
    #     else:
    #         info_parts = []
            
    #         # Basic info
    #         birth_date = fighter.get('birth_date', '')
    #         birth_place = fighter.get('birth_place', '')
    #         if birth_date and birth_place:
    #             info_parts.append(f"{name} was born on {birth_date} in {birth_place}")
    #         elif birth_date:
    #             info_parts.append(f"{name} was born on {birth_date}")
    #         elif birth_place:
    #             info_parts.append(f"{name} was born in {birth_place}")
            
    #         # Death info
    #         death_date = fighter.get('death_date', '')
    #         if death_date:
    #             info_parts.append(f"died on {death_date}")
            
    #         # Contributions
    #         contributions = fighter.get('contributions', [])
    #         if contributions:
    #             info_parts.append(f"Known for: {', '.join(contributions[:2])}")
            
    #         # Biography
    #         biography = fighter.get('biography', '')
    #         if biography:
    #             info_parts.append(f"Biography: {biography[:200]}...")
            
    #         if info_parts:
    #             return '. '.join(info_parts) + '.'
    #         else:
    #             return f"I have limited information about {name}."
    
    # def generate_fallback_response(self, message):
    #     """Generate fallback response when no fighter is found"""
    #     return ("I couldn't find information about that freedom fighter. "
    #             "Try asking about famous figures like Gandhi, Nehru, Bhagat Singh, "
    #             "Subhas Chandra Bose, or other Indian freedom fighters.")
    
    def show_typing_indicator(self):
        """Show typing indicator"""
        self.is_loading = True
        self.send_btn.config(text="Sending...", state=tk.DISABLED, fg="white",bg="#6366f1",                # Keep your purple background
        activeforeground="white",
        activebackground="#6366f1",
        disabledforeground="white" )
        
        # Add typing indicator to chat
        self.messages_text.config(state=tk.NORMAL)
        self.messages_text.insert(tk.END, "🤖 Thinking...\n", 'bot_message')
        self.messages_text.config(state=tk.DISABLED)
        self.messages_text.see(tk.END)
    
    def hide_typing_indicator(self):
        """Hide typing indicator"""
        self.is_loading = False
        self.send_btn.config(
        text="Send",
        state=tk.NORMAL,
        fg="white",
        bg="#6366f1",
        activeforeground="white",
        activebackground="#6366f1"
    )

        # Remove typing indicator
        self.messages_text.config(state=tk.NORMAL)
        self.messages_text.delete("end-2l", "end-1l")
        self.messages_text.config(state=tk.DISABLED)

    
    def handle_response(self, response):
        """Handle response from chatbot"""
        self.hide_typing_indicator()
        
        # Add bot response
        current_time = self.format_time(datetime.now())
        bot_message = {
            'content': response,
            'isUser': False,
            'info': current_time
        }
        
        self.add_message_to_chat(response, False, current_time)
        self.all_sessions[self.current_session_id].append(bot_message)
        
        # Update sessions list
        self.update_sessions_list()
        
        # Focus back on input
        self.message_entry.focus()
    
    def add_message_to_chat(self, content, is_user, info, scroll_to_bottom=True):
        """Add message to chat display"""
        self.messages_text.config(state=tk.NORMAL)  # ⬅️ Add this line to allow inserting
    
        if is_user:
            self.messages_text.insert(tk.END, f"You: {content}\n", 'user_message')
        else:
            self.messages_text.insert(tk.END, f"Bot: {content}\n", 'bot_message')

        self.messages_text.insert(tk.END, f"    {info}\n\n", 'time_info')

        #self.messages_text.config(state=tk.DISABLED)  # ⬅️ Optional: re-disable after insert
    
        if scroll_to_bottom:
            self.messages_text.see(tk.END)


    def format_time(self, dt):
            """Format timestamp"""
            return dt.strftime("%I:%M %p")
    
    def clear_current_chat(self):
        """Clear current chat session"""
        if messagebox.askyesno("Clear Chat", "Are you sure you want to clear this chat?"):
            self.all_sessions[self.current_session_id] = []
            self.clear_chat_messages()
            self.show_welcome_message()
            self.update_sessions_list()

def main():
    root = tk.Tk()
    app = SocialcienceChatbot(root)
    root.mainloop()

if __name__ == "__main__":
    main()

