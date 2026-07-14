# DearDiary

A full-stack journal application with AI-powered insights and NLP analysis capabilities.

## 📋 Project Overview

DearDiary is an intelligent journaling application that combines a modern React frontend with a sophisticated Python backend powered by machine learning. The application helps users capture their daily thoughts and provides AI-driven insights through natural language processing and emotion analysis.

## 🏗️ Architecture

### Project Structure

```
DearDiary/
├── frontend/          # React-based user interface
├── backend/           # Python API and core logic
├── model/             # ML model and experiments
├── database/          # Database schema and configuration
└── package.json       # Root package configuration
```

### Components

#### **Frontend** (`frontend/`)
- React-based single-page application
- Pages:
  - **Login/Register**: User authentication
  - **Journal**: Main journaling interface with entry creation
  - **Calendar**: Visual calendar view of entries
  - **History**: Browse past entries
  - **Flashback**: Revisit memories from specific dates
  - **Insights**: AI-generated insights and analytics
  - **Happy Memories**: Collection of positive moments
  - **Visualize**: Data visualization dashboard

#### **Backend** (`backend/`)
- Flask/FastAPI server
- Components:
  - `main.py`: Application entry point
  - `database.py`: Database connection and management
  - `db_utils.py`: Database utility functions
  - `entity_extractor.py`: NLP entity extraction
  - `nlp_model.py`: Natural language processing
  - `requirements.txt`: Python dependencies

#### **ML Model** (`model/`)
- Experiment tracking and model training
- Components:
  - `config.py`: Model configuration
  - `data_loader/`: Dataset loading utilities
  - `models/`: Model factory and trainer
  - `experiments/`: Experiment runner
  - `results/`: Exported models and checkpoints
  - `utils/`: Helper utilities

#### **Database** (`database/`)
- `schema.sql`: Database schema definition

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 14+
- npm or yarn
- SQLite/PostgreSQL (database)

### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Create and activate virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the backend server:**
   ```bash
   python main.py
   ```

### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Run development server:**
   ```bash
   npm run dev
   ```

   Or use the provided script:
   ```bash
   node run-dev.js
   ```

4. **Build for production:**
   ```bash
   npm run build
   ```

## 🧠 ML Model

### Training

Run experiments to train and evaluate models:

```bash
cd model
python experiments/run_experiment.py
```

### Model Export

The trained model is exported to `model/results/exported_model/` with:
- Model weights (`model.safetensors`)
- Tokenizer configuration
- Label mappings
- Model configuration

## 📊 Features

- ✍️ **Journal Entries**: Create, read, and manage diary entries
- 🗓️ **Calendar View**: Visualize entries across dates
- 🎯 **Insights**: AI-generated insights from journal content
- 🔍 **Entity Extraction**: Automatic extraction of people, places, and concepts
- 💭 **Emotion Analysis**: Detect and track emotional patterns
- 🌟 **Memory Collections**: Organize and revisit happy memories
- 📈 **Analytics Dashboard**: Visualize patterns and trends
- 🔐 **User Authentication**: Secure login and registration

## 🛠️ Technology Stack

### Frontend
- **React**: UI library
- **CSS Modules**: Component-scoped styling
- **JavaScript (ES6+)**: Core language

### Backend
- **Python**: Server language
- **Flask/FastAPI**: Web framework
- **SQLite/PostgreSQL**: Database

### ML/NLP
- **Transformers**: NLP models
- **PyTorch**: Deep learning framework
- **Hugging Face**: Model hub

## 📦 Dependencies

Key Python packages (see `backend/requirements.txt`):
- Flask/FastAPI
- SQLAlchemy
- Transformers
- PyTorch
- Pandas
- NLTK

Key Node packages (see `frontend/package.json`):
- React
- React Router
- Axios

## 🗄️ Database Schema

The database schema is defined in `database/schema.sql`. Key tables include:
- Users: User account information
- Entries: Journal entries content
- Entities: Extracted entities from entries
- Emotions: Emotion analysis results

## 🚦 Development Workflow

1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature
   ```

2. Make your changes and commit:
   ```bash
   git add .
   git commit -m "Add your feature"
   ```

3. Push to remote:
   ```bash
   git push origin feature/your-feature
   ```

4. Create a pull request on GitHub

## 📝 Configuration

### Frontend Config
Edit `frontend/src/config.js` for API endpoints and settings.

### Backend Config
Edit `model/config.py` for model parameters and server settings.

## 🔍 API Endpoints

The backend provides RESTful API endpoints for:
- User authentication (login, register, logout)
- Journal entry management (CRUD operations)
- Entity extraction and analysis
- Emotion detection
- Insights generation

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to your fork
5. Submit a pull request

## 📄 License

This project is part of a thesis/capstone project. Please ensure compliance with institutional guidelines.

## 📧 Contact & Support

For questions or issues, please open an issue on GitHub.

---

**Built with ❤️ for better self-reflection and personal growth**
