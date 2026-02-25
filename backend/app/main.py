"""ReflectAI Backend - FastAPI Main Application

A privacy-first AI-powered sentiment analysis API for journal entries.
"""
import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.services.sentiment import SentimentAnalyzer
from app.services.insights import InsightsGenerator
from app.core.config import settings
from app.core.logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Global instances
sentiment_analyzer: SentimentAnalyzer | None = None
insights_generator: InsightsGenerator | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager"""
    global sentiment_analyzer, insights_generator
    
    logger.info("Starting ReflectAI Backend...")
    
    # Initialize ML models on startup
    try:
        sentiment_analyzer = SentimentAnalyzer()
        insights_generator = InsightsGenerator()
        logger.info("ML models loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load ML models: {e}")
        raise
    
    yield
    
    # Cleanup on shutdown
    logger.info("Shutting down ReflectAI Backend...")


# Initialize FastAPI app
app = FastAPI(
    title="ReflectAI API",
    description="Privacy-first sentiment analysis and mood tracking API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class JournalEntry(BaseModel):
    """Journal entry for sentiment analysis"""
    text: str = Field(..., min_length=1, max_length=5000, description="Journal entry text")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "Today was amazing! I felt so productive and happy."
            }
        }


class SentimentResponse(BaseModel):
    """Sentiment analysis result"""
    mood: str = Field(..., description="Detected mood")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score")
    emotions: dict[str, float] | None = Field(None, description="Detailed emotion scores")


class InsightsRequest(BaseModel):
    """Request for generating insights"""
    moods: list[str] = Field(..., min_items=1, description="List of recent moods")
    
    class Config:
        json_schema_extra = {
            "example": {
                "moods": ["sad", "anxious", "neutral", "sad", "stressed"]
            }
        }


class InsightsResponse(BaseModel):
    """Insights and suggestions"""
    suggestion: str = Field(..., description="Personalized suggestion")
    mood_trend: str = Field(..., description="Overall mood trend")
    dominant_emotion: str = Field(..., description="Most frequent emotion")


# API Endpoints
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to ReflectAI API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", tags=["Health"], response_model=dict)
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "ok",
        "environment": settings.ENVIRONMENT,
        "model_loaded": sentiment_analyzer is not None,
        "insights_available": insights_generator is not None,
    }


@app.post(
    "/api/v1/analyze",
    response_model=SentimentResponse,
    status_code=status.HTTP_200_OK,
    tags=["Sentiment Analysis"],
)
async def analyze_sentiment(entry: JournalEntry):
    """
    Analyze sentiment of a journal entry.
    
    Returns mood classification and confidence score.
    """
    if not sentiment_analyzer:
        logger.error("Sentiment analyzer not initialized")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Sentiment analysis service unavailable"
        )
    
    try:
        # Analyze the journal text
        result = sentiment_analyzer.analyze(entry.text)
        logger.info(f"Sentiment analyzed: {result['mood']} (confidence: {result['confidence']:.2f})")
        return result
    
    except Exception as e:
        logger.error(f"Error analyzing sentiment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze sentiment"
        )


@app.post(
    "/api/v1/insights",
    response_model=InsightsResponse,
    status_code=status.HTTP_200_OK,
    tags=["Insights"],
)
async def generate_insights(request: InsightsRequest):
    """
    Generate personalized insights based on mood history.
    
    Provides suggestions and trend analysis.
    """
    if not insights_generator:
        logger.error("Insights generator not initialized")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Insights generation service unavailable"
        )
    
    try:
        insights = insights_generator.generate(request.moods)
        logger.info(f"Insights generated for {len(request.moods)} mood entries")
        return insights
    
    except Exception as e:
        logger.error(f"Error generating insights: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate insights"
        )


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    logger.warning(f"HTTP {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal server error", "status_code": 500}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
