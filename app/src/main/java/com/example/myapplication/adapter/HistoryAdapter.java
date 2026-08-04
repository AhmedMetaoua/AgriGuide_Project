package com.example.myapplication.adapter;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;

import com.example.myapplication.R;
import com.example.myapplication.model.InsectHistoryEntity;

import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Locale;

public class HistoryAdapter extends RecyclerView.Adapter<HistoryAdapter.ViewHolder> {
    private List<InsectHistoryEntity> historyList = new ArrayList<>();
    private final SimpleDateFormat dateFormat = new SimpleDateFormat("dd/MM/yyyy HH:mm", Locale.getDefault());

    public void setHistory(List<InsectHistoryEntity> history) {
        this.historyList = history;
        notifyDataSetChanged();
    }

    @NonNull
    @Override
    public ViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext()).inflate(R.layout.item_insect_history, parent, false);
        return new ViewHolder(view);
    }

    @Override
    public void onBindViewHolder(@NonNull ViewHolder holder, int position) {
        InsectHistoryEntity insect = historyList.get(position);
        holder.tvName.setText(insect.getInsectName());
        holder.tvDate.setText(dateFormat.format(new Date(insect.getTimestamp())));
        holder.tvImpact.setText(insect.getImpactDetails());
        
        if (insect.isHarmful()) {
            holder.itemView.setBackgroundResource(R.drawable.bg_history_item_alert);
        } else {
            holder.itemView.setBackgroundResource(R.drawable.bg_history_item_normal);
        }
    }

    @Override
    public int getItemCount() {
        return historyList.size();
    }

    static class ViewHolder extends RecyclerView.ViewHolder {
        TextView tvName, tvDate, tvImpact;

        ViewHolder(View view) {
            super(view);
            tvName = view.findViewById(R.id.tv_history_name);
            tvDate = view.findViewById(R.id.tv_history_date);
            tvImpact = view.findViewById(R.id.tv_history_impact);
        }
    }
}
