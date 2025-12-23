#version 330 core

in vec3 fragNormal;
in vec3 fragPosition;
in vec2 fragTexCoord;

uniform vec3 color;
uniform vec3 lightDir;
uniform vec3 lightColor;
uniform vec3 viewPos;
uniform bool useLighting;

out vec4 fragColor;

void main() {
    if (useLighting) {
        // Ambient lighting
        float ambientStrength = 0.3;
        vec3 ambient = ambientStrength * lightColor;
        
        // Diffuse lighting
        vec3 norm = normalize(fragNormal);
        vec3 lightDirection = normalize(-lightDir);
        float diff = max(dot(norm, lightDirection), 0.0);
        vec3 diffuse = diff * lightColor;
        
        // Specular lighting (optional, for shiny surfaces)
        float specularStrength = 0.5;
        vec3 viewDir = normalize(viewPos - fragPosition);
        vec3 reflectDir = reflect(-lightDirection, norm);
        float spec = pow(max(dot(viewDir, reflectDir), 0.0), 32.0);
        vec3 specular = specularStrength * spec * lightColor;
        
        // Combine lighting
        vec3 result = (ambient + diffuse + specular) * color;
        fragColor = vec4(result, 1.0);
    } else {
        // Simple color rendering (for lines, etc.)
        fragColor = vec4(color, 1.0);
    }
}

