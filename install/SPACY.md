- The script now recognizes Python 3.13 as a special case that requires more careful handling
- It attempts multiple installation strategies in sequence for Python 3.13+:
  1. First tries to use prebuilt wheels from compatible versions (3.5.3, 3.5.2, etc.)
  2. Falls back to regular installation if wheels are available
  3. As a last resort, attempts to install a legacy version (3.0.9) which may have fewer dependencies

2. **Virtual Environment Support**:
   - Added a `--venv PATH` option to create and use a Python virtual environment
   - This isolates the spaCy installation from the system Python, preventing conflicts

3. **More Installation Options**:
   - Added `--binary` and `--no-binary` flags to control whether to use prebuilt wheels
   - Improved error handling with better fallback mechanisms
   - More verbose logging to help diagnose installation issues

4. **Better Compatibility Testing**:
   - More robust version detection and compatibility checks
   - Improved verification that tests spaCy functionality even if model loading fails
   - Fallback to basic functionality test if model installation fails

### How to Use

The updated script can be run with:

```bash
sudo bash spacy.sh
```

Or with custom options like:

```bash
sudo bash spacy.sh --venv ~/spacy-env --version 3.5.3
```

