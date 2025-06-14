"""Background license validation for Knova AI SDK"""

import asyncio
import threading
from datetime import datetime, timedelta
from typing import Optional, Callable, Any
import logging

from .license import LicenseValidator, LicenseTier

logger = logging.getLogger(__name__)


class LicenseBackgroundValidator:
    """Handles periodic license validation in the background"""
    
    def __init__(self, license_validator: LicenseValidator):
        self.license_validator = license_validator
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._validation_callback: Optional[Callable[[bool, Any], None]] = None
        
        # Validation intervals based on tier (in seconds)
        self.VALIDATION_INTERVALS = {
            LicenseTier.FREE: 24 * 3600,      # 24 hours
            LicenseTier.PRO: 6 * 3600,        # 6 hours
            LicenseTier.ENTERPRISE: 12 * 3600  # 12 hours
        }
        
        # Expiration warning thresholds (days before expiration)
        self.WARNING_THRESHOLDS = [30, 7, 1]
        
    def set_validation_callback(self, callback: Callable[[bool, Any], None]):
        """Set callback to be called after each validation"""
        self._validation_callback = callback
        
    def start(self):
        """Start background validation"""
        if self._running:
            logger.warning("Background validator already running")
            return
            
        self._running = True
        
        # Create a new event loop in a separate thread
        self._thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self._thread.start()
        
        logger.info("Background license validator started")
        
    def stop(self):
        """Stop background validation"""
        if not self._running:
            return
            
        self._running = False
        
        # Cancel the task if it exists
        if self._task and not self._task.done():
            self._task.cancel()
            
        # Stop the event loop
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
            
        # Wait for thread to finish
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
            
        logger.info("Background license validator stopped")
        
    def _run_event_loop(self):
        """Run the event loop in a separate thread"""
        try:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            
            # Create the validation task
            self._task = self._loop.create_task(self._validate_periodically())
            
            # Run the event loop
            self._loop.run_forever()
            
        except Exception as e:
            logger.error(f"Error in background validation thread: {e}")
        finally:
            if self._loop:
                self._loop.close()
                
    async def _validate_periodically(self):
        """Periodically validate license based on tier"""
        first_run = True
        
        while self._running:
            try:
                # Perform validation
                is_valid = await self.license_validator.validate()
                
                # Get license info for warnings
                license_info = await self.license_validator.get_license_info()
                
                # Check for expiration warnings
                if license_info and license_info.expires_at:
                    self._check_expiration_warnings(license_info.expires_at)
                
                # Call callback if set
                if self._validation_callback:
                    try:
                        self._validation_callback(is_valid, license_info)
                    except Exception as e:
                        logger.error(f"Error in validation callback: {e}")
                
                # Log validation result
                if not is_valid:
                    logger.warning("Background license validation failed")
                elif not first_run:  # Don't log on first run to reduce noise
                    logger.debug("Background license validation successful")
                    
                first_run = False
                
                # Calculate next validation interval based on tier
                tier = self.license_validator.get_tier()
                interval = self.VALIDATION_INTERVALS.get(
                    LicenseTier(tier),
                    self.VALIDATION_INTERVALS[LicenseTier.FREE]
                )
                
                # Wait for next validation
                await asyncio.sleep(interval)
                
            except asyncio.CancelledError:
                # Task was cancelled, exit gracefully
                break
            except Exception as e:
                logger.error(f"Error during background validation: {e}")
                # Wait before retrying
                await asyncio.sleep(60)  # Retry after 1 minute on error
                
    def _check_expiration_warnings(self, expires_at: datetime):
        """Check and log license expiration warnings"""
        days_until_expiry = (expires_at - datetime.now()).days
        
        for threshold in self.WARNING_THRESHOLDS:
            if days_until_expiry == threshold:
                logger.warning(
                    f"License expires in {days_until_expiry} days. "
                    f"Please renew your license to avoid service interruption."
                )
                break
            elif days_until_expiry < threshold and days_until_expiry > 0:
                # Already past this threshold but not yet at next one
                continue
                
        if days_until_expiry <= 0:
            logger.error("License has expired. Please renew immediately.")
            
    def force_validation(self):
        """Force an immediate validation (runs in background)"""
        if not self._running or not self._loop:
            logger.warning("Background validator not running")
            return
            
        # Schedule immediate validation
        future = asyncio.run_coroutine_threadsafe(
            self._perform_immediate_validation(),
            self._loop
        )
        
        # Don't wait for result, let it run in background
        logger.info("Scheduled immediate background validation")
        
    async def _perform_immediate_validation(self):
        """Perform immediate validation"""
        try:
            is_valid = await self.license_validator.validate()
            license_info = await self.license_validator.get_license_info()
            
            if self._validation_callback:
                self._validation_callback(is_valid, license_info)
                
            logger.info(f"Immediate validation completed: {'valid' if is_valid else 'invalid'}")
            
        except Exception as e:
            logger.error(f"Error during immediate validation: {e}")
            
    def is_running(self) -> bool:
        """Check if background validator is running"""
        return self._running and self._thread and self._thread.is_alive()
        
    def get_next_validation_time(self) -> Optional[datetime]:
        """Get estimated time of next validation"""
        if not self.is_running():
            return None
            
        cache_status = self.license_validator.get_cache_status()
        if cache_status.get('cache_expires'):
            # Next validation will happen when cache expires
            return datetime.fromisoformat(cache_status['cache_expires'])
            
        return None