#include <iostream>
#include <string>
#include <map>

/**
 * @brief Ce programme permet de muter les stream audios en arrière-plan 
 * et de jouer le son dont le titre est donné en paramètre 
 * 
 * @param argc titre de la musique et volume auquel elle doit être amenée
 * @author Paolo RONDOT - paolo.rondot@gmail.com
 * @version 1
 * @date 19/07/2022
 */

int main(int argc, char *argv[])
{
	FILE *fp;
 	char path[1035];

 	/* Open the command for reading. */
 	fp = popen("pactl list sink-inputs | grep -e 'Sink Input' -e 'Volume'", "r");
 	if (fp == NULL) {
 		printf("Failed to run command\n" );
  	}
  	/* Read the output a line at a time - output it. */
	std::string answer;
  	while (fgets(path, sizeof(path), fp) != NULL) {
		answer += path;
  	}
	std::cout<<answer<<std::endl;
  	/* close */
  	pclose(fp);
	size_t found = 0;
	std::map<std::string, std::string> volumes;
	while(1){
		std::string id, vol;
		found = answer.find("Input #", found);
		if(found == std::string::npos) break;
		found = found+7;
		id += answer[found];
		while(answer[found+1]>47 && answer[found+1]<58)
			id+=answer[++found];
		found = answer.find("front-left: ", found);
		found = answer.find("/", found);
		found += 1;
		vol += answer[found];
		while(answer[found+1] != '/')
			vol += answer[++found];
		volumes[id] = vol;
	}
	for(auto itr = volumes.begin(); itr != volumes.end(); ++itr){
		std::cout<<itr->first<<": "<<itr->second<<std::endl;
		std::string volumeCmd = "pactl set-sink-input-volume ";
		volumeCmd += itr->first;
		volumeCmd += " ";
		volumeCmd += argv[2];
		std::cout<<volumeCmd<<std::endl;
		system(volumeCmd.c_str());
	}
	//std::cin.get();
	std::string playSound = "mpg123 /home/pi/sounds/";
	playSound += argv[1];
	system(playSound.c_str());
	for(auto itr = volumes.begin(); itr != volumes.end(); ++itr){
		std::cout<<itr->first<<": "<<itr->second<<std::endl;
		std::string volumeCmd = "pactl set-sink-input-volume ";
		volumeCmd += itr->first;
		volumeCmd += " ";
		volumeCmd += itr->second;
		std::cout<<volumeCmd<<std::endl;
		system(volumeCmd.c_str());
	}
  	return 0;
}
