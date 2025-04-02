# Krishna Chatbot

This project creates a web-based chatbot that answers questions as Lord Krishna, strictly referring to the Bhagavad Gita and other sacred texts. The chatbot provides wisdom and guidance in the voice of Krishna, with proper citations to the source texts.

## Features

- Interactive chat interface with a spiritual theme
- File upload system for adding custom sacred texts (supports JSON, Markdown, and plain text)
- Natural language processing to match questions with relevant verses
- Response generation in the voice/style of Lord Krishna
- Citation display showing the source text, chapter, and verse
- Mobile-friendly responsive design

## Project Structure

```
krishna-chatbot/
├── public/                 # Static frontend files
│   ├── index.html          # Main HTML page
│   ├── admin.html          # Main admin page
│   ├── app.js              # Frontend JavaScript
│   └── krishna-theme.css   # CSS styles
│   ├── krishna.png         # Krishna's pfp
│   ├── user.png            # User's pfp
│   ├── vrindavan.jpg       # Vrindavan's background
├── data/                   # Default knowledge base
│   └── bhagavad_gita.json  # Bhagavad Gita verses in JSON format
├── file-processor.js       # Handles parsing and processing text files
├── llm-helper.js           # Handles api calls with llm
├── server.js               # Express backend server
└── package.json            # Project dependencies
```

## Setup and Installation

1. Clone this repository
2. Install dependencies:
   ```
   npm install
   ```
3. Start the server:
   ```
   npm start
   ```
4. Open your browser and navigate to `http://localhost:3000`

## Adding Custom Texts

You can add custom sacred texts to the chatbot in several ways:

1. **Through the Web Interface**: Use the "Add Text" button in the admin panel to upload files.

2. **Directly in the data folder**: Add JSON files with the following structure:
   ```json
   [
     {
       "chapter": 1,
       "verse": 1,
       "text": "The verse text goes here",
       "keywords": ["keyword1", "keyword2"]
     }
   ]
   ```

3. **Text Format**: For plain text files, use the following format:
   ```
   Chapter 1
   Verse 1: The verse text goes here

   Verse 2: Another verse text
   ```

4. **Markdown Format**: For markdown files, use:
   ```md
   # Chapter 1
   
   ## Verse 1
   The verse text goes here
   
   ## Verse 2
   Another verse text
   ```

## Customization

- Edit the CSS styles to change the appearance
- Modify the response templates in `file-processor.js` to change Krishna's speech patterns
- Add more sophisticated NLP by enhancing the keyword extraction in `file-processor.js`

## Technologies Used

- **Frontend**: HTML, CSS, JavaScript
- **Backend**: Node.js, Express
- **NLP**: Natural.js library for text processing
- **File Handling**: Multer for file uploads

## License

MIT License
