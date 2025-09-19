{{/*
Common helpers
*/}}
{{- define "onos.fullname" -}}
{{- if .Values.nameOverride -}}
{{- .Values.nameOverride -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name .Chart.Name -}}
{{- end -}}
{{- end -}}

{{- define "onos.selectorName" -}}
{{- default "onos" .Values.selectorName -}}
{{- end -}}
