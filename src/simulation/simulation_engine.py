"""
Simulation engine for missile defense scenarios
"""

import numpy as np
import time
from typing import List, Optional
from src.simulation.missile import Missile
from src.simulation.interceptor import Interceptor


class SimulationEngine:
    """Manages simulation state and updates"""
    
    def __init__(self, config, algorithm_type: str):
        """
        Initialize simulation engine
        
        Args:
            config: Configuration dictionary
            algorithm_type: "old" or "new"
        """
        self.config = config
        self.algorithm_type = algorithm_type
        self.algorithm_config = config['algorithms'][algorithm_type]
        
        # Simulation state
        self.missiles: List[Missile] = []
        self.interceptors: List[Interceptor] = []
        self.defense_system_pos = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        
        # Timing
        self.last_update_time = None
        self.simulation_speed = 1.0
        self.is_running = False
        self.is_paused = False
        
        # Response delay tracking (non-blocking)
        self.missile_response_times = {}  # missile -> time when response can happen
        
        # Statistics
        self.missiles_destroyed = 0
        self.interceptors_launched = 0
        self.missiles_total_spawned = 0  # Total missiles spawned (for counter)
        self.missiles_intercepted = 0    # Engaged missiles successfully intercepted
        self.missiles_missed = 0         # Engaged missiles that were not intercepted
        self.engaged_missiles = 0        # Missiles that entered Destroy phase
        self.engaged_missile_ids = set() # Track engaged missile IDs
        self.missed_missiles = []        # List of missed missile events for visual feedback
        self.start_time = None
        
        # Interception time tracking per missile (simulation-time based, not wall-clock)
        # Values are stored in seconds and advanced only while the simulation is running
        self.missile_interception_times = {}  # missile_id -> interception_time (seconds)
        self.current_interception_times = {}  # missile_id -> current elapsed time since detection (seconds)
        
        # Response time tracking per phase
        self.phase_response_times = {
            "Tracing": [],      # List of times spent in Tracing phase
            "Warning": [],      # List of times spent in Warning phase
            "Destroy": []       # List of times from Destroy phase start to interceptor launch
        }
        
        # Track phase entry times for each missile
        self.missile_phase_times = {}  # missile_id -> {phase: entry_time}
        
        # Phase distance thresholds (distance from defense system)
        # Phases are now distance-based, not time-based
        self.tracing_range = config['simulation'].get('tracing_range', 80.0)
        self.warning_range = config['simulation'].get('warning_range', 50.0)
        self.destroy_range = config['simulation'].get('destroy_range', 30.0)
        self.detection_range = config['simulation']['detection_range']
        
        # Phase processing delays (algorithm-specific response times)
        # These affect how quickly the system responds within each phase
        if algorithm_type == "old":
            self.phase_processing_delays = {
                "Tracing": 0.5,    # 500ms to process detection
                "Warning": 0.8,    # 800ms to calculate trajectory
                "Destroy": 1.2     # 1200ms to launch interceptor
            }
        else:  # new
            self.phase_processing_delays = {
                "Tracing": 0.05,   # 50ms to process detection (much faster)
                "Warning": 0.08,    # 80ms to calculate trajectory (much faster)
                "Destroy": 0.15    # 150ms to launch interceptor (much faster)
            }
        
        # Phase statistics
        self.phase_stats = {
            "Tracing": {"active": 0, "progress": 0.0},
            "Warning": {"active": 0, "progress": 0.0},
            "Destroy": {"active": 0, "progress": 0.0}
        }
        
        # Continuous spawning
        self.last_spawn_time = None
        self.spawn_interval = 3.0  # Spawn new missile every 3 seconds
        self.max_concurrent_missiles = 10  # Maximum missiles at once
        
        # Scenario and movement patterns
        # This is used to vary missile routes by scenario
        self.current_scenario = "single"
        self.movement_patterns = {
            "single": "straight",
            "wave": "curved",
            "saturation": "zigzag",
            "custom": "straight",  # Default, can be overridden by custom_movement_pattern
        }
        self.custom_movement_pattern = "straight"  # User-selected pattern for custom scenario
        
        # Threat type (missiles or drones)
        self.threat_type = "missiles"  # "missiles" or "drones"
        
        # Processing performance tracking
        self.detections_per_scan = 0  # Number of RF reflections detected in current scan
        self.processing_time_per_scan = 0.0  # Processing time in ms for current scan
        self.last_scan_time = None
        self.scan_interval = 0.1  # Scan every 100ms
        
    def start(self, threat_count: int = None, seed: int = None):
        """Start simulation with given threat count
        
        Args:
            threat_count: Number of initial missiles to spawn
            seed: Optional random seed for synchronized spawning
        """
        if threat_count is None:
            threat_count = self.config['simulation']['default_threat_count']
            
        self.is_running = True
        self.is_paused = False
        self.start_time = time.time()
        self.last_update_time = time.time()
        self.last_spawn_time = time.time()
        
        # Clear previous state
        self.missiles.clear()
        self.interceptors.clear()
        self.missiles_destroyed = 0
        self.interceptors_launched = 0
        self.missiles_total_spawned = 0
        self.missiles_intercepted = 0
        self.missiles_missed = 0
        self.engaged_missiles = 0
        self.engaged_missile_ids = set()
        self.missile_response_times.clear()
        self.phase_response_times = {
            "Tracing": [],
            "Warning": [],
            "Destroy": []
        }
        self.missile_phase_times.clear()
        self.missile_interception_times.clear()
        self.current_interception_times.clear()
        
        # Store seed for continuous spawning
        self.spawn_seed = seed
        
        # Spawn initial batch of missiles
        self._spawn_missiles(threat_count, seed)
        
    def pause(self):
        """Pause simulation"""
        self.is_paused = True
        
    def resume(self):
        """Resume simulation"""
        self.is_paused = False
        self.last_update_time = time.time()
        
    def reset(self):
        """Reset simulation"""
        self.is_running = False
        self.is_paused = False
        self.missiles.clear()
        self.interceptors.clear()
        self.missiles_destroyed = 0
        self.interceptors_launched = 0
        self.missiles_intercepted = 0
        self.missiles_missed = 0
        self.engaged_missiles = 0
        self.engaged_missile_ids.clear()
        if hasattr(self, 'missed_missiles'):
            self.missed_missiles.clear()
        else:
            self.missed_missiles = []
        self.last_update_time = None
        
    def update(self):
        """Update simulation state"""
        if not self.is_running or self.is_paused:
            return
            
        current_time = time.time()
        if self.last_update_time is None:
            self.last_update_time = current_time
            return
            
        # Calculate delta time
        delta_time = (current_time - self.last_update_time) * self.simulation_speed
        self.last_update_time = current_time
        
        # Continuous spawning - maintain constant missile count
        # Spawn new missiles immediately to maintain max_concurrent_missiles count
        active_missile_count = len([m for m in self.missiles if m.active and not m.destroyed])
        # Spawn immediately if below target count (no interval wait) - use while loop to fill up
        while active_missile_count < self.max_concurrent_missiles:
            # Use seed for synchronized spawning if available, but add variation for random positions
            spawn_seed = getattr(self, 'spawn_seed', None)
            if spawn_seed is not None:
                # Add current time and missile count to ensure unique positions
                # This keeps synchronization between old/new but ensures random positions
                unique_seed = spawn_seed + active_missile_count + int(current_time * 1000) % 10000
            else:
                # No base seed - use completely random spawning
                unique_seed = int(current_time * 1000) + active_missile_count + len(self.missiles)
            self._spawn_single_missile(unique_seed)
            self.last_spawn_time = current_time
            active_missile_count = len([m for m in self.missiles if m.active and not m.destroyed])
        
        # Simulate radar scan and processing (every scan_interval)
        if self.last_scan_time is None or (current_time - self.last_scan_time) >= self.scan_interval:
            # Calculate detections per scan (RF reflections)
            # Each active missile generates multiple reflections based on scenario
            active_missile_count = len([m for m in self.missiles if m.active and not m.destroyed])
            
            # Base reflections per missile/drone (varies by scenario and threat type)
            base_reflections_per_threat = {
                "single": 5 if self.threat_type == "missiles" else 3,
                "wave": 8 if self.threat_type == "missiles" else 5,
                "saturation": 12 if self.threat_type == "missiles" else 8,
                "custom": 6 if self.threat_type == "missiles" else 4,
            }
            base_reflections = base_reflections_per_threat.get(self.current_scenario, 6)
            
            # Add random variation (±20%)
            import random
            variation = random.uniform(0.8, 1.2)
            self.detections_per_scan = int(active_missile_count * base_reflections * variation)
            
            # Calculate processing time per scan based on algorithm and detections
            # Old algorithm: exponential growth with detections (slow)
            # New algorithm: linear growth with detections (fast)
            if self.algorithm_type == "old":
                # Conventional: exponential growth - 1000-10000x slower
                # Base time increases exponentially with detections
                base_time_ms = 50.0  # Base processing time
                # Exponential: time = base * (detections^1.5) / 10
                self.processing_time_per_scan = base_time_ms * ((self.detections_per_scan ** 1.5) / 10.0)
                # Add random variation
                self.processing_time_per_scan *= random.uniform(0.9, 1.1)
                # Cap at reasonable max (30 seconds)
                self.processing_time_per_scan = min(30000.0, max(100.0, self.processing_time_per_scan))
            else:  # new algorithm
                # SA+H: linear growth - 1000-10000x faster
                # Base time is much lower and grows linearly
                base_time_ms = 0.05  # Base processing time (50 microseconds)
                # Linear: time = base * detections
                self.processing_time_per_scan = base_time_ms * self.detections_per_scan
                # Add tiny random variation
                self.processing_time_per_scan *= random.uniform(0.95, 1.05)
                # Cap at reasonable max (50ms)
                self.processing_time_per_scan = min(50.0, max(0.1, self.processing_time_per_scan))
            
            self.last_scan_time = current_time
        
        # Update missile phases first (needs current_time)
        self._update_phases(current_time)
        
        # Update missiles and track interception times (simulation-time based)
        # Attacking missiles move at the same speed for both algorithms
        for missile in self.missiles[:]:  # Copy list to avoid modification during iteration
            missile.update(delta_time)
            missile_id = id(missile)
            
            # Check if missile reached center without interception (missed)
            # Mark as destroyed so it gets processed in the destroyed check below
            distance_to_center = np.linalg.norm(missile.position - self.defense_system_pos)
            if distance_to_center < 2.0 and missile.active and not missile.destroyed:
                # Missile reached center - mark as destroyed if it was engaged
                if missile_id in self.engaged_missile_ids:
                    missile.destroyed = True
                    missile.active = False
                    # Don't count here - will be counted in destroyed check below

            if missile.destroyed:
                self.missiles_destroyed += 1

                # If this missile was engaged (entered Destroy phase), classify as intercepted or missed
                if missile_id in self.engaged_missile_ids:
                    if getattr(missile, "intercepted", False):
                        # Successfully intercepted
                        self.missiles_intercepted += 1
                    else:
                        # Missile was destroyed but not intercepted - it's a miss
                        # (either reached center or was destroyed by reaching target without interception)
                        self.missiles_missed += 1
                        # Store missed missile info for visual feedback (only for old algorithm)
                        if self.algorithm_type == "old":
                            if not hasattr(self, 'missed_missiles'):
                                self.missed_missiles = []
                            self.missed_missiles.append({
                                'position': self.defense_system_pos.copy(),
                                'time': time.time()
                            })
                    self.engaged_missile_ids.discard(missile_id)

                # Record interception time (elapsed seconds accumulated while running)
                if missile_id in self.current_interception_times:
                    interception_time = self.current_interception_times[missile_id]
                    self.missile_interception_times[missile_id] = interception_time
                    del self.current_interception_times[missile_id]
                
                # Record tracing time if missile was destroyed while still in Tracing phase
                # (missiles that are destroyed before transitioning to Warning)
                if missile_id in self.missile_phase_times and "Tracing" in self.missile_phase_times[missile_id]:
                    # Check if it never entered Warning phase
                    if "Warning" not in self.missile_phase_times[missile_id]:
                        tracing_start = self.missile_phase_times[missile_id]["Tracing"]
                        # Use current_time from update loop (already defined above)
                        tracing_time = current_time - tracing_start
                        if tracing_time > 0:
                            self.phase_response_times["Tracing"].append(tracing_time)
                            print(f"[{self.algorithm_type}] Recorded tracing time: {tracing_time:.3f}s for destroyed missile")

            elif missile.detected:
                # Advance current interception time for active detected missiles
                # Initialize if first time seen
                if missile_id not in self.current_interception_times:
                    self.current_interception_times[missile_id] = 0.0
                # Increase by delta_time (seconds); this automatically freezes when paused
                self.current_interception_times[missile_id] += delta_time

        # Remove destroyed/inactive missiles
        self.missiles = [m for m in self.missiles if m.active and not m.destroyed]
        
        # Clean up interception times for missiles that got away
        active_missile_ids = {id(m) for m in self.missiles}
        self.current_interception_times = {
            mid: t for mid, t in self.current_interception_times.items()
            if mid in active_missile_ids
        }
        
        # Update interceptors (apply speed multiplier for new algorithm - faster trajectory analysis)
        speed_multiplier = 1.0 if self.algorithm_type == "old" else 1.5  # New algorithm interceptors move faster due to faster analysis
        for interceptor in self.interceptors[:]:
            interceptor.update(delta_time * speed_multiplier)
            
        # Remove inactive interceptors
        self.interceptors = [i for i in self.interceptors if i.active]
        
        # Launch interceptors for missiles in Destroy phase
        self._process_threats(delta_time)
        
    def _spawn_missiles(self, count: int, seed: int = None):
        """Spawn incoming missiles at random positions far from center
        
        Args:
            count: Number of missiles to spawn
            seed: Optional random seed for synchronized spawning
        """
        # Use seed if provided for synchronization
        if seed is not None:
            import random
            rng_state = random.getstate()
            random.seed(seed)
            np_rng_state = np.random.get_state()
            np.random.seed(seed)
        
        for i in range(count):
            # Spawn from random position far from center
            # Add index to seed to ensure variation even with same base seed
            if seed is not None:
                # Re-seed with index variation for each missile
                random.seed(seed + i * 1000)
                np.random.seed(seed + i * 1000)
            angle = np.random.uniform(0, 2 * np.pi)  # Random angle
            distance = np.random.uniform(60.0, 90.0)  # Far from center (was 20.0)
            height = np.random.uniform(10.0, 25.0)  # Random height
            
            start_pos = np.array([
                distance * np.cos(angle),
                height,
                distance * np.sin(angle)
            ], dtype=np.float32)
            
            # Target is near defense system (with some randomness)
            target_pos = self.defense_system_pos + np.array([
                np.random.uniform(-5, 5),
                0.0,
                np.random.uniform(-5, 5)
            ], dtype=np.float32)
            
            # Speed varies by threat type: missiles are faster, drones are slower
            if self.threat_type == "drones":
                speed = self.config['simulation']['default_speed'] * 2.0  # Drones are slower
            else:
                speed = self.config['simulation']['default_speed'] * 3.0  # Missiles are faster
            
            # Get movement pattern based on scenario
            # For custom scenario, use user-selected pattern
            if self.current_scenario == "custom":
                movement_pattern = self.custom_movement_pattern
            else:
                movement_pattern = self.movement_patterns.get(self.current_scenario, "straight")
            
            # Drones tend to have more erratic movement (zigzag/spiral) even in simple scenarios
            if self.threat_type == "drones" and movement_pattern == "straight" and self.current_scenario != "custom":
                # Make drones slightly more erratic even in "straight" scenarios (but not for custom)
                import random
                if random.random() < 0.5:  # 50% chance for drones to zigzag even in simple scenarios
                    movement_pattern = "zigzag"
            
            missile = Missile(start_pos, target_pos, speed, self.config, movement_pattern)
            # Store threat type in missile for visual differences
            missile.threat_type = self.threat_type
            self.missiles.append(missile)
            self.missiles_total_spawned += 1
        
        # Restore random state if seed was used
        if seed is not None:
            random.setstate(rng_state)
            np.random.set_state(np_rng_state)
            
        # print(f"[{self.algorithm_type}] Spawned {count} missiles")
    
    def _spawn_single_missile(self, seed: int = None):
        """Spawn a single missile for continuous spawning with random position"""
        # Pass seed directly to _spawn_missiles - it will handle randomization
        self._spawn_missiles(1, seed)
            
    def _update_phases(self, current_time: float):
        """Update phase states for all missiles based on distance from defense system"""
        # Reset phase stats
        self.phase_stats = {
            "Tracing": {"active": 0, "progress": 0.0},
            "Warning": {"active": 0, "progress": 0.0},
            "Destroy": {"active": 0, "progress": 0.0}
        }
        
        for missile in self.missiles:
            if not missile.active or missile.destroyed:
                continue
                
            # Calculate distance from defense system (2D distance on X-Z plane)
            pos_2d = missile.position - self.defense_system_pos
            distance = np.sqrt(pos_2d[0]**2 + pos_2d[2]**2)
            
            # Phase transitions based on distance thresholds
            old_phase = getattr(missile, 'phase', 'Tracing')
            
            # Phase 1: Tracing - Detect and track missile (far range)
            if distance < self.detection_range and not missile.detected:
                missile.detected = True
                missile.phase = "Tracing"
                missile.phase_start_time = current_time
                # Start tracking interception time (elapsed seconds, begins at 0)
                missile_id = id(missile)
                self.current_interception_times[missile_id] = 0.0
                # Track phase entry for Tracing (important for tracing time calculation)
                if missile_id not in self.missile_phase_times:
                    self.missile_phase_times[missile_id] = {}
                self.missile_phase_times[missile_id]["Tracing"] = current_time
            
            if missile.detected:
                missile_id = id(missile)
                
                # Determine phase based on distance
                if distance >= self.tracing_range:
                    # Still in Tracing phase (far away)
                    new_phase = "Tracing"
                    if old_phase != "Tracing":
                        missile.phase_start_time = current_time
                        # Track phase entry
                        if missile_id not in self.missile_phase_times:
                            self.missile_phase_times[missile_id] = {}
                        self.missile_phase_times[missile_id]["Tracing"] = current_time
                elif distance >= self.warning_range:
                    # Enter Warning phase (medium range)
                    new_phase = "Warning"
                    if old_phase != "Warning":
                        missile.phase_start_time = current_time
                        # Track phase transition and record Tracing time
                        if missile_id not in self.missile_phase_times:
                            self.missile_phase_times[missile_id] = {}
                        if "Tracing" in self.missile_phase_times[missile_id] and old_phase == "Tracing":
                            tracing_time = current_time - self.missile_phase_times[missile_id]["Tracing"]
                            self.phase_response_times["Tracing"].append(tracing_time)
                        self.missile_phase_times[missile_id]["Warning"] = current_time
                elif distance >= self.destroy_range:
                    # Enter Destroy phase (close range)
                    new_phase = "Destroy"
                    if old_phase != "Destroy":
                        missile.phase_start_time = current_time
                        # Track phase transition and record Warning time
                        if missile_id not in self.missile_phase_times:
                            self.missile_phase_times[missile_id] = {}
                        if "Warning" in self.missile_phase_times[missile_id] and old_phase == "Warning":
                            warning_time = current_time - self.missile_phase_times[missile_id]["Warning"]
                            self.phase_response_times["Warning"].append(warning_time)
                        self.missile_phase_times[missile_id]["Destroy"] = current_time
                        # Mark missile as engaged when it first enters Destroy phase
                        if missile_id not in self.engaged_missile_ids:
                            self.engaged_missiles += 1
                            self.engaged_missile_ids.add(missile_id)
                else:
                    # Very close - stay in Destroy phase
                    new_phase = "Destroy"
                
                missile.phase = new_phase
                
                # Calculate progress within current phase based on distance
                if missile.phase == "Tracing":
                    # Progress: 100% at warning_range, 0% at detection_range
                    if self.detection_range > self.tracing_range:
                        progress = 100.0 * (1.0 - (distance - self.tracing_range) / (self.detection_range - self.tracing_range))
                        progress = max(0.0, min(100.0, progress))
                    else:
                        progress = 100.0 if distance <= self.tracing_range else 0.0
                elif missile.phase == "Warning":
                    # Progress: 100% at destroy_range, 0% at warning_range
                    if self.warning_range > self.destroy_range:
                        progress = 100.0 * (1.0 - (distance - self.destroy_range) / (self.warning_range - self.destroy_range))
                        progress = max(0.0, min(100.0, progress))
                    else:
                        progress = 100.0 if distance <= self.warning_range else 0.0
                elif missile.phase == "Destroy":
                    # Progress: 100% at success_threshold, 0% at destroy_range
                    success_threshold = self.config['simulation']['success_threshold']
                    if self.destroy_range > success_threshold:
                        progress = 100.0 * (1.0 - (distance - success_threshold) / (self.destroy_range - success_threshold))
                        progress = max(0.0, min(100.0, progress))
                    else:
                        progress = 100.0 if distance <= self.destroy_range else 0.0
                
                # Update phase statistics
                self.phase_stats[missile.phase]["active"] += 1
                self.phase_stats[missile.phase]["progress"] = max(
                    self.phase_stats[missile.phase]["progress"], progress
                )
    
    def _process_threats(self, delta_time: float):
        """Process threats and launch interceptors (algorithm-specific)"""
        if self.algorithm_type == "old":
            self._process_threats_old(delta_time)
        else:
            self._process_threats_new(delta_time)
            
    def _process_threats_old(self, delta_time: float):
        """Old algorithm: Sequential processing - only launch in Destroy phase"""
        current_time = time.time()
        
        # Process one threat at a time (sequential)
        for missile in self.missiles:
            if missile.active and not missile.destroyed and missile.phase == "Destroy":
                # Check if interceptor already launched
                if any(i.target_missile == missile and i.active 
                      for i in self.interceptors):
                    continue
                
                # Check if processing delay has passed (algorithm-specific delay)
                missile_id = id(missile)
                if missile_id not in self.missile_phase_times or "Destroy" not in self.missile_phase_times[missile_id]:
                    continue
                
                destroy_start_time = self.missile_phase_times[missile_id]["Destroy"]
                time_in_destroy = current_time - destroy_start_time
                processing_delay = self.phase_processing_delays["Destroy"]
                
                if time_in_destroy >= processing_delay:
                    # Old algorithm: Sometimes miss due to slower computation (lower accuracy)
                    import random
                    accuracy = self.algorithm_config.get('success_rate', 0.85)
                    if random.random() < accuracy:
                        # Launch interceptor
                        interceptor = Interceptor(
                            self.defense_system_pos,
                            missile,
                            self.config['simulation']['default_speed'] * 
                            self.config['simulation']['interceptor_speed_multiplier'],
                            self.config,
                            np.array(self.algorithm_config['color'], dtype=np.float32)
                        )
                        self.interceptors.append(interceptor)
                        self.interceptors_launched += 1
                        
                        # Record Destroy phase response time
                        self.phase_response_times["Destroy"].append(time_in_destroy)
                    else:
                        # Missed - interceptor not launched (simulating slower computation error)
                        pass
                    
                    # Clean up tracking
                    if missile_id in self.missile_phase_times:
                        del self.missile_phase_times[missile_id]
                    
                    break  # Only process one at a time (sequential)
                        
    def _process_threats_new(self, delta_time: float):
        """New algorithm: Parallel processing - launch in Destroy phase for all"""
        current_time = time.time()
        
        # Process all threats simultaneously (parallel)
        for missile in self.missiles:
            if missile.active and not missile.destroyed and missile.phase == "Destroy":
                # Check if interceptor already launched
                if any(i.target_missile == missile and i.active 
                      for i in self.interceptors):
                    continue
                
                # Check if processing delay has passed (algorithm-specific delay)
                missile_id = id(missile)
                if missile_id not in self.missile_phase_times or "Destroy" not in self.missile_phase_times[missile_id]:
                    continue
                
                destroy_start_time = self.missile_phase_times[missile_id]["Destroy"]
                time_in_destroy = current_time - destroy_start_time
                processing_delay = self.phase_processing_delays["Destroy"]
                
                if time_in_destroy >= processing_delay:
                    # New algorithm: Always launch interceptor once processing delay is met
                    # This makes the logical success ratio 100% (misses only if missile escapes
                    # before an interceptor can physically reach it, which is rare with current settings)
                    interceptor = Interceptor(
                        self.defense_system_pos,
                        missile,
                        self.config['simulation']['default_speed'] * 
                        self.config['simulation']['interceptor_speed_multiplier'],
                        self.config,
                        np.array(self.algorithm_config['color'], dtype=np.float32)
                    )
                    self.interceptors.append(interceptor)
                    self.interceptors_launched += 1
                    
                    # Record Destroy phase response time
                    self.phase_response_times["Destroy"].append(time_in_destroy)
                    
                    # Clean up tracking
                    if missile_id in self.missile_phase_times:
                        del self.missile_phase_times[missile_id]
                    
                    # Continue processing all threats (parallel)
                        
    def get_missiles(self) -> List[Missile]:
        """Get list of active missiles"""
        return self.missiles
        
    def get_interceptors(self) -> List[Interceptor]:
        """Get list of active interceptors"""
        return self.interceptors
        
    def get_statistics(self) -> dict:
        """Get simulation statistics"""
        # Always calculate active counts (needed for return statement)
        active_missiles = len(self.missiles)
        active_interceptors = len(self.interceptors)
        
        # Calculate dynamic CPU usage based on active missiles and phases
        # Only change CPU when simulation is running
        if not self.is_running or self.is_paused:
            # Return 0% CPU when not running (initial state)
            dynamic_cpu = 0.0
        else:
            base_cpu = self.algorithm_config['cpu_overhead'] * 100
            
            # CPU increases with more active threats and processing
            cpu_multiplier = 1.0 + (active_missiles * 0.05) + (active_interceptors * 0.02)
            dynamic_cpu = min(100.0, base_cpu * cpu_multiplier)
            
            # Add some realistic variation
            import random
            cpu_variation = random.uniform(-2.0, 2.0)
            dynamic_cpu = max(10.0, min(100.0, dynamic_cpu + cpu_variation))
        
        # Calculate average response times per phase
        avg_response_times = {}
        for phase in ["Tracing", "Warning", "Destroy"]:
            times = self.phase_response_times[phase]
            if times:
                avg_response_times[phase] = sum(times) / len(times) * 1000  # Convert to ms
            else:
                avg_response_times[phase] = 0.0
        
        # Calculate total average response time
        total_response_time = sum(avg_response_times.values())
        
        # Calculate average interception time
        avg_interception_time = 0.0
        if self.missile_interception_times:
            avg_interception_time = sum(self.missile_interception_times.values()) / len(self.missile_interception_times) * 1000  # Convert to ms
        
        # Get current interception times for active missiles (already in seconds)
        current_times = {}
        for missile_id, elapsed_sec in self.current_interception_times.items():
            current_times[missile_id] = elapsed_sec * 1000.0  # Convert to ms
        
        # Success rate calculation: intercepted / (intercepted + missed) * 100
        # This calculates success rate based on actual interception attempts
        total_interception_attempts = self.missiles_intercepted + self.missiles_missed
        if total_interception_attempts > 0:
            logical_success_rate = (self.missiles_intercepted / total_interception_attempts) * 100.0
        else:
            logical_success_rate = 0.0  # No attempts yet

        # Count missiles in each phase for progress bars
        missiles_in_tracing = len([m for m in self.missiles if m.active and not m.destroyed and m.phase == "Tracing"])
        missiles_in_warning = len([m for m in self.missiles if m.active and not m.destroyed and m.phase == "Warning"])
        missiles_in_destroy = len([m for m in self.missiles if m.active and not m.destroyed and m.phase == "Destroy"])
        
        # Threat limits: old = 15, new = 30
        threat_limit = 15 if self.algorithm_type == "old" else 30

        return {
            'missiles_active': active_missiles,
            'missiles_destroyed': self.missiles_destroyed,
            'missiles_total_spawned': self.missiles_total_spawned,
            'missiles_engaged': self.engaged_missiles,
            'missiles_intercepted': self.missiles_intercepted,
            'missiles_missed': self.missiles_missed,
            'interceptors_active': active_interceptors,
            'interceptors_launched': self.interceptors_launched,
            'success_rate': logical_success_rate,
            'phase_stats': self.phase_stats.copy(),
            'missiles_in_tracing': missiles_in_tracing,
            'missiles_in_warning': missiles_in_warning,
            'missiles_in_destroy': missiles_in_destroy,
            'threat_limit': threat_limit,
            'cpu_usage': dynamic_cpu,
            'response_times': avg_response_times,
            'total_response_time': total_response_time,
            'phase_response_times_raw': {
                phase: [t * 1000 for t in times]  # Convert to ms
                for phase, times in self.phase_response_times.items()
            },
            'avg_interception_time': avg_interception_time,
            'current_interception_times': current_times,
            'detections_per_scan': self.detections_per_scan,
            'processing_time_per_scan': self.processing_time_per_scan
        }

