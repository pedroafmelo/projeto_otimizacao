# !/bin/zsh
if [ ! -d "./.venv" ]; then

    if [ -x "$(command -v python)" ]; then
        echo "Building python environment...."
        python -m venv .venv
        if [[ "$OSTYPE" == "msys" ]]; then
           source ./.venv/Script/activate 
        else
            source ./.venv/bin/activate
        fi
        
        pip install -r ./requirements.txt
    fi

    if [ -x "$(command -v python3)" ]; then
        echo "Building python environment...."
        python3 -m venv .venv
        if [[ "$OSTYPE" == "msys" ]]; then
           source ./.venv/Script/activate 
        else
            source ./.venv/bin/activate
        fi
        pip install -r ./requirements.txt
    fi

else
    if [ -x "$(command -v python)" ]; then
        echo "Updating python environment...."
        python -m venv .venv
        if [[ "$OSTYPE" == "msys" ]]; then
           source ./.venv/Script/activate 
        else
            source ./.venv/bin/activate
        fi
        pip install -r ./requirements.txt
    fi

    if [ -x "$(command -v python3)" ]; then
        echo "Updating python environment...."
        if [[ "$OSTYPE" == "msys" ]]; then
           source ./.venv/Script/activate 
        else
            source ./.venv/bin/activate
        fi
        pip install -r ./requirements.txt
    fi  
fi