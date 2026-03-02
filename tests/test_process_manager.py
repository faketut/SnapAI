import pytest
import os
import sys
import subprocess
from unittest.mock import MagicMock, patch
from src.process_manager.process_manager import ProcessManager

def test_process_manager_init():
    """Test ProcessManager initialization"""
    manager = ProcessManager()
    assert manager.server_proc is None
    assert manager.overlay_proc is None
    assert os.path.isdir(manager.base_path)

@patch('subprocess.Popen')
def test_process_manager_create_process(mock_popen):
    """Test ProcessManager creates correctly configured subprocesses"""
    manager = ProcessManager()
    
    # Mock Popen return value
    mock_proc = MagicMock()
    mock_popen.return_value = mock_proc
    
    proc = manager._create_process('--server')
    
    # Verify Popen was called with expected arguments
    assert mock_popen.called
    args = mock_popen.call_args[0][0]
    assert '--server' in args
    assert sys.executable in args
    assert proc == mock_proc

@patch('src.process_manager.process_manager.ProcessManager._check_port_available')
@patch('src.process_manager.process_manager.ProcessManager._check_overlay_running')
@patch('src.process_manager.process_manager.ProcessManager._create_process')
def test_process_manager_start_stop(mock_create, mock_overlay_check, mock_port_check):
    """Test ProcessManager starting and stopping logic"""
    manager = ProcessManager()
    
    # Mock system state
    mock_port_check.return_value = True
    mock_overlay_check.return_value = False
    
    # Mock process instances
    mock_server = MagicMock()
    mock_server.poll.return_value = None
    mock_overlay = MagicMock()
    mock_overlay.poll.return_value = None
    mock_create.side_effect = [mock_server, mock_overlay]
    
    with patch('time.sleep'), patch('psutil.Process') as mock_psutil_proc:
        # Mock psutil process behavior
        mock_psutil_instance = MagicMock()
        mock_psutil_proc.return_value = mock_psutil_instance
        mock_psutil_instance.children.return_value = []
        
        # Only test start_processes to avoid blocking in run()
        manager.start_processes()
        
        assert manager.server_proc == mock_server
        assert manager.overlay_proc == mock_overlay
        assert mock_create.call_count == 2
        
        # Test stop logic
        manager.cleanup()
        
        # Give threading a tiny bit of time if needed, though cleanup joins
        mock_server.terminate.assert_called()
        mock_overlay.terminate.assert_called()
