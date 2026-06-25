import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../services/chatbot_api.dart';
import '../services/token_storage.dart';
import '../services/app_localizations.dart';

// AI Chatbot screen for multilingual agricultural assistance
class ChatbotPage extends StatefulWidget {
  const ChatbotPage({super.key});

  static const String routeName = '/chatbot';

  @override
  State<ChatbotPage> createState() => _ChatbotPageState();
}

class _ChatbotPageState extends State<ChatbotPage> {
  final _messageController = TextEditingController();
  final _scrollController = ScrollController();
  final _chatbotApi = ChatbotApi();
  final _tokenStorage = const TokenStorage();
  
  List<ChatMessage> _messages = [];
  bool _isLoading = false;
  bool _isSending = false;
  String _userLanguage = 'en';

  @override
  void initState() {
    super.initState();
    _initializeChat();
  }

  @override
  void dispose() {
    _messageController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  Future<void> _initializeChat() async {
    // Load user language preference
    final profile = await _tokenStorage.readUserProfile();
    if (profile != null) {
      final preferredLanguage = profile['preferred_language']?.toString();
      if (preferredLanguage != null && preferredLanguage.isNotEmpty) {
        setState(() {
          _userLanguage = preferredLanguage;
        });
      }
    }

    // Load conversation history
    await _loadChatHistory();

    // Send welcome message if no history
    if (_messages.isEmpty) {
      _addWelcomeMessage();
    }
  }

  Future<void> _loadChatHistory() async {
    try {
      setState(() {
        _isLoading = true;
      });

      final accessToken = await _tokenStorage.readAccessToken();
      if (accessToken == null || accessToken.isEmpty) {
        return;
      }

      final history = await _chatbotApi.getChatHistory(
        accessToken: accessToken,
        limit: 50,
      );

      if (mounted) {
        setState(() {
          _messages = history
              .map((h) => [
                    ChatMessage(
                      content: h['message'] ?? '',
                      isUser: true,
                      timestamp: DateTime.tryParse(h['timestamp'] ?? '') ?? DateTime.now(),
                    ),
                    ChatMessage(
                      content: h['response'] ?? '',
                      isUser: false,
                      timestamp: DateTime.tryParse(h['timestamp'] ?? '') ?? DateTime.now(),
                      intent: h['intent'],
                    ),
                  ])
              .expand((pair) => pair)
              .toList();
        });
      }
    } catch (e) {
      debugPrint('Failed to load chat history: $e');
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  void _addWelcomeMessage() {
    final welcomeMessages = {
      'en': 'Hello! I\'m your AI farming assistant. I can help you with crop diseases, weather information, farming advice, and more. How can I assist you today?',
      'hi': 'नमस्ते! मैं आपका एआई कृषि सहायक हूं। मैं फसल की बीमारियों, मौसम की जानकारी, खेती की सलाह और भी बहुत कुछ में आपकी मदद कर सकता हूं। आज मैं आपकी कैसे सहायता कर सकता हूं?',
      'ta': 'வணக்கம்! நான் உங்கள் AI விவசாய உதவியாளர். பயிர் நோய்கள், வானிலை தகவல், விவசாய ஆலோசனை மற்றும் பல விஷயங்களில் உங்களுக்கு உதவ முடியும். இன்று நான் உங்களுக்கு எவ்வாறு உதவ முடியும்?',
      'te': 'నమస్కారం! నేను మీ AI వ్యవసాయ సహాయకుడిని. పంట వ్యాధులు, వాతావరణ సమాచారం, వ్యవసాయ సలహా మరియు మరిన్నింటిలో మీకు సహాయం చేయగలను. ఈ రోజు నేను మీకు ఎలా సహాయం చేయగలను?',
      'kn': 'ನಮಸ್ಕಾರ! ನಾನು ನಿಮ್ಮ AI ಕೃಷಿ ಸಹಾಯಕ. ಬೆಳೆ ರೋಗಗಳು, ಹವಾಮಾನ ಮಾಹಿತಿ, ಕೃಷಿ ಸಲಹೆ ಮತ್ತು ಇತರ ವಿಷಯಗಳಲ್ಲಿ ನಿಮಗೆ ಸಹಾಯ ಮಾಡಬಹುದು. ಇಂದು ನಾನು ನಿಮಗೆ ಹೇಗೆ ಸಹಾಯ ಮಾಡಬಹುದು?',
      'ml': 'നമസ്കാരം! ഞാൻ നിങ്ങളുടെ AI കൃഷി സഹായിയാണ്. വിള രോഗങ്ങൾ, കാലാവസ്ഥാ വിവരങ്ങൾ, കൃഷി ഉപദേശം എന്നിവയിലും മറ്റും നിങ്ങളെ സഹായിക്കാൻ എനിക്ക് കഴിയും. ഇന്ന് ഞാൻ നിങ്ങളെ എങ്ങനെ സഹായിക്കാം?',
    };

    final welcomeText = welcomeMessages[_userLanguage] ?? welcomeMessages['en']!;
    
    setState(() {
      _messages.add(ChatMessage(
        content: welcomeText,
        isUser: false,
        timestamp: DateTime.now(),
        intent: 'welcome',
      ));
    });

    _scrollToBottom();
  }

  Future<void> _sendMessage() async {
    final message = _messageController.text.trim();
    if (message.isEmpty || _isSending) return;

    // Add user message to chat
    final userMessage = ChatMessage(
      content: message,
      isUser: true,
      timestamp: DateTime.now(),
    );

    setState(() {
      _messages.add(userMessage);
      _isSending = true;
    });

    _messageController.clear();
    _scrollToBottom();

    try {
      final accessToken = await _tokenStorage.readAccessToken();
      if (accessToken == null || accessToken.isEmpty) {
        throw Exception('Please log in to use the chatbot');
      }

      // Send message to backend
      final response = await _chatbotApi.sendMessage(
        accessToken: accessToken,
        message: message,
        language: _userLanguage,
      );

      // Add bot response to chat
      final botMessage = ChatMessage(
        content: response['response'] ?? 'Sorry, I couldn\'t process your message.',
        isUser: false,
        timestamp: DateTime.now(),
        intent: response['intent'],
        confidence: response['confidence']?.toDouble(),
      );

      if (mounted) {
        setState(() {
          _messages.add(botMessage);
        });
        _scrollToBottom();
      }
    } catch (e) {
      // Add error message
      final errorMessage = ChatMessage(
        content: context.t('Sorry, I\'m having trouble right now. Please try again later.'),
        isUser: false,
        timestamp: DateTime.now(),
        intent: 'error',
      );

      if (mounted) {
        setState(() {
          _messages.add(errorMessage);
        });
        _scrollToBottom();
      }
    } finally {
      if (mounted) {
        setState(() {
          _isSending = false;
        });
      }
    }
  }

  void _scrollToBottom() {
    Future.delayed(const Duration(milliseconds: 100), () {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  Future<void> _clearHistory() async {
    try {
      final accessToken = await _tokenStorage.readAccessToken();
      if (accessToken != null) {
        await _chatbotApi.clearChatHistory(accessToken: accessToken);
      }

      setState(() {
        _messages.clear();
      });

      _addWelcomeMessage();

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(context.t('Chat history cleared'))),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(context.t('Failed to clear chat history'))),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;

    return Scaffold(
      appBar: AppBar(
        title: Text(context.t('AI Farm Assistant')),
        backgroundColor: scheme.primary,
        foregroundColor: scheme.onPrimary,
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.clear_all),
            onPressed: _clearHistory,
            tooltip: context.t('Clear chat'),
          ),
        ],
      ),
      body: Column(
        children: [
          // Chat messages area
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : ListView.builder(
                    controller: _scrollController,
                    padding: const EdgeInsets.all(16.0),
                    itemCount: _messages.length,
                    itemBuilder: (context, index) {
                      final message = _messages[index];
                      return _buildMessageBubble(message, scheme);
                    },
                  ),
          ),
          
          // Message input area
          Container(
            padding: const EdgeInsets.all(16.0),
            decoration: BoxDecoration(
              color: scheme.surface,
              border: Border(top: BorderSide(color: scheme.outline.withOpacity(0.2))),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.1),
                  offset: const Offset(0, -2),
                  blurRadius: 4,
                ),
              ],
            ),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _messageController,
                    decoration: InputDecoration(
                      hintText: context.t('Type your message...'),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(24),
                        borderSide: BorderSide.none,
                      ),
                      filled: true,
                      fillColor: scheme.surfaceVariant,
                      contentPadding: const EdgeInsets.symmetric(
                        horizontal: 20,
                        vertical: 12,
                      ),
                    ),
                    maxLines: null,
                    textCapitalization: TextCapitalization.sentences,
                    onSubmitted: (_) => _sendMessage(),
                  ),
                ),
                const SizedBox(width: 12),
                FloatingActionButton.small(
                  onPressed: _isSending ? null : _sendMessage,
                  backgroundColor: scheme.primary,
                  foregroundColor: scheme.onPrimary,
                  child: _isSending
                      ? SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: scheme.onPrimary,
                          ),
                        )
                      : const Icon(Icons.send),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMessageBubble(ChatMessage message, ColorScheme scheme) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4.0),
      child: Row(
        mainAxisAlignment: message.isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (!message.isUser) ...[
            CircleAvatar(
              radius: 16,
              backgroundColor: scheme.primary,
              child: Icon(
                Icons.smart_toy,
                size: 18,
                color: scheme.onPrimary,
              ),
            ),
            const SizedBox(width: 8),
          ],
          Flexible(
            child: Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: message.isUser ? scheme.primary : scheme.surfaceVariant,
                borderRadius: BorderRadius.circular(18).copyWith(
                  bottomLeft: message.isUser ? const Radius.circular(18) : const Radius.circular(4),
                  bottomRight: message.isUser ? const Radius.circular(4) : const Radius.circular(18),
                ),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    message.content,
                    style: TextStyle(
                      color: message.isUser ? scheme.onPrimary : scheme.onSurfaceVariant,
                      fontSize: 16,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(
                        _formatTime(message.timestamp),
                        style: TextStyle(
                          color: (message.isUser ? scheme.onPrimary : scheme.onSurfaceVariant)
                              .withOpacity(0.7),
                          fontSize: 12,
                        ),
                      ),
                      if (message.intent != null && !message.isUser) ...[
                        const SizedBox(width: 4),
                        Icon(
                          _getIntentIcon(message.intent!),
                          size: 12,
                          color: scheme.onSurfaceVariant.withOpacity(0.7),
                        ),
                      ],
                    ],
                  ),
                ],
              ),
            ),
          ),
          if (message.isUser) ...[
            const SizedBox(width: 8),
            CircleAvatar(
              radius: 16,
              backgroundColor: scheme.secondary,
              child: Icon(
                Icons.person,
                size: 18,
                color: scheme.onSecondary,
              ),
            ),
          ],
        ],
      ),
    );
  }

  String _formatTime(DateTime dateTime) {
    final now = DateTime.now();
    final difference = now.difference(dateTime);
    
    if (difference.inDays > 0) {
      return '${difference.inDays}d ago';
    } else if (difference.inHours > 0) {
      return '${difference.inHours}h ago';
    } else if (difference.inMinutes > 0) {
      return '${difference.inMinutes}m ago';
    } else {
      return 'now';
    }
  }

  IconData _getIntentIcon(String intent) {
    switch (intent) {
      case 'crop disease diagnosis':
        return Icons.local_hospital;
      case 'weather inquiry':
        return Icons.wb_sunny;
      case 'farming advice':
        return Icons.agriculture;
      case 'fertilizer guidance':
        return Icons.eco;
      case 'irrigation tips':
        return Icons.water_drop;
      case 'pest control':
        return Icons.bug_report;
      case 'seasonal farming':
        return Icons.calendar_today;
      default:
        return Icons.chat;
    }
  }
}

class ChatMessage {
  final String content;
  final bool isUser;
  final DateTime timestamp;
  final String? intent;
  final double? confidence;

  ChatMessage({
    required this.content,
    required this.isUser,
    required this.timestamp,
    this.intent,
    this.confidence,
  });
}