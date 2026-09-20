class StateManager:
    def __init__(self):
        self.previous_states = {}

    def check_state_change(self, device_name, current_state):
        prev_state = self.previous_states.get(device_name, "OK")

        if prev_state == current_state:
            return None

        self.previous_states[device_name] = current_state

        if current_state in ["WARNING", "CRITICAL"]:
            return "ALERT"

        if current_state == "OK" and prev_state in ["WARNING", "CRITICAL"]:
            return "RECOVERY"

        return None
