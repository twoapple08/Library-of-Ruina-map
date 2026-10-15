#version 330
#extension GL_ARB_separate_shader_objects : require

#include <minecraft:fog.glsl>
#include <minecraft:dynamictransforms.glsl>

uniform sampler2D Sampler0;

layout(location = 0) in float sphericalVertexDistance;
layout(location = 1) in float cylindricalVertexDistance;
layout(location = 2) in vec4 vertexColor;
layout(location = 3) in vec2 texCoord0;

layout(location = 0) out vec4 fragColor;

// 그린 하늘: 안개 없이 텍스처 × 꼭짓점 색 그대로 (FogColor 는 묶음 배치를 맞추려고만 참조)
void main() {
    vec4 color = texture(Sampler0, texCoord0) * vertexColor * ColorModulator;
    fragColor = vec4(color.rgb, 1.0) + FogColor * 0.0 * (sphericalVertexDistance + cylindricalVertexDistance);
}
